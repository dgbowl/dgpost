"""
dgpost.main
===========

Module containing the execution functions for dgpost.

"""
import argparse
import logging
from importlib import metadata
import pandas as pd
import copy

from dgpost.utils import parse, load, extract, transform, save, plot


def run(path: str, patch: str = None) -> tuple[dict, dict]:
    """
    Main API execution function. Loads the `recipe` from the provided ``path``,
    and processes the following entries, in order:

    - :mod:`~dgpost.utils.load`,
    - :mod:`~dgpost.utils.extract`,
    - :mod:`~dgpost.utils.transform`,
    - :mod:`~dgpost.utils.plot`,
    - :mod:`~dgpost.utils.save`.

    .. note::

        When saving a table, its metadata entry will contain dgpost version
        information, as well as a copy of the `recipe` used to create the saved
        object.

    Parameters
    ----------
    path
        Path to the job specification, passed to :func:`dgpost.utils.parse`

    Returns
    -------
    (datagrams, tables)
        A tuple of the loaded datagrams and exported & transformed tables.

    """
    spec = parse(path)

    meta = {
        "provenance": f"dgpost-{metadata.version('dgpost')}",
        "recipe": copy.deepcopy(spec),
    }

    datagrams = {}
    tables = {}
    l = spec.pop("load")
    for el in l:
        if patch is None:
            fp = el["path"]
        else:
            fp = el["path"].replace("$patch", patch).replace("$PATCH", patch)
        if el["type"] == "datagram":
            datagrams[el["as"]] = load(fp, el["check"], el["type"])
        else:
            tables[el["as"]] = load(fp, el["check"], el["type"])

    e = spec.get("extract", [])
    for el in e:
        saveas = el.pop("into")
        if "from" in el and el["from"] is not None:
            objname = el.pop("from")
            if objname in datagrams:
                obj = datagrams[objname]
            elif objname in tables:
                obj = tables[objname]
            else:
                raise RuntimeError(
                    f"Object name '{objname}' is neither a valid datagram nor table."
                )
        else:
            obj = None

        if saveas not in tables:
            index = None
        else:
            index = tables[saveas].index.tolist()

        newdf = extract(obj, el, index)

        if saveas in tables:
            temp = pd.concat([tables[saveas], newdf], axis=1)
            temp.attrs = tables[saveas].attrs
            temp.attrs["units"].update(newdf.attrs["units"])
            tables[saveas] = temp
        else:
            tables[saveas] = newdf

    t = spec.get("transform", [])
    for el in t:
        transform(tables[el["table"]], el["with"], el["using"])

    p = spec.get("plot", [])
    for el in p:
        table = tables[el.pop("table")]
        plot(table, **el)

    s = spec.get("save", [])
    for el in s:
        save(tables[el["table"]], el["as"], el.get("type"), el.get("sigma", True), meta)
    return datagrams, tables


def run_with_arguments():
    """
    Main external execution function.

    This is the function executed when dgpost is launched using the executable. It
    processes the ``--version`` command, sets the loglevel based on the number of
    ``-v/-q`` passed, and forwards the ``infile`` argument to :func:`run`.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="version",
        version=f'%(prog)s version {metadata.version("dgpost")}',
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity by one level.",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="Decrease verbosity by one level.",
    )

    parser.add_argument(
        "--patch",
        "-p",
        help="Patch the YAML infile using the provided file name.",
        default=None,
    )

    parser.add_argument(
        "infile",
        help="File containing the YAML to be processed by dgpost.",
        default=None,
    )

    args = parser.parse_args()

    loglevel = min(max(30 - (10 * args.verbose) + (10 * args.quiet), 10), 50)
    logging.basicConfig(level=loglevel)
    logging.debug(f"loglevel set to '{logging._levelToName[loglevel]}'")

    run(args.infile, patch=args.patch)
