"""
dgpost.main
===========

Module containing the execution functions for dgpost.

"""
import argparse
import logging
from importlib import metadata
import copy
import requests
import json
from packaging import version

from dgpost.utils import parse, load, extract, transform, save, plot, pivot
from dgpost.utils.helpers import combine_tables

logger = logging.getLogger(__name__)


def version_check(project="dgpost"):
    url = f"https://pypi.org/pypi/{project}/json"
    try:
        res = requests.get(url, timeout=1)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.debug(f"Version check could not proceed due to Exception={e}.")
        return
    jsdata = json.loads(res.text)
    versions = sorted([version.parse(i) for i in jsdata["releases"].keys()])
    latest = versions[-1]
    current = version.parse(metadata.version(project))
    if latest > current:
        logger.warning("You are using an out-of-date version of '%s'. ", project)
        logger.info(
            "The latest version is '%s', the current version is '%s'.", latest, current
        )
        logger.info(
            "Consider updating using: pip install --upgrade %s==%s", project, latest
        )
    else:
        logger.debug("Your version of '%s' is up-to-date.", project)


def run(path: str, patch: str = None) -> tuple[dict, dict]:
    """
    Main API execution function. Loads the `recipe` from the provided ``path``,
    patches the file paths specified within the `recipe`, if necessary, and
    processes the following entries, in order:

    - :mod:`~dgpost.utils.load`,
    - :mod:`~dgpost.utils.extract`,
    - :mod:`~dgpost.utils.pivot`,
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

    logger.info("Processing 'load'.")
    l = spec.pop("load")
    for el in l:
        if patch is None:
            fp = el["path"]
        else:
            fp = el["path"].replace("$patch", patch).replace("$PATCH", patch)
        if el["type"] == "datagram":
            datagrams[el["as"]] = load(fp, el.get("check", None), el["type"])
        else:
            tables[el["as"]] = load(fp, None, el["type"])

    logger.info("Processing 'extract'.")
    e = spec.get("extract", [])
    for el in e:
        saveas = el.pop("into")
        if "from" in el and el["from"] is not None:
            objname = el.pop("from")
            logger.debug("extracting from '%s' into '%s'", objname, saveas)
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
            temp = combine_tables(tables[saveas], newdf)
            temp.attrs = tables[saveas].attrs
            temp.attrs["units"].update(newdf.attrs["units"])
            tables[saveas] = temp
        else:
            tables[saveas] = newdf

    logger.info("Processing 'pivot'.")
    p = spec.get("pivot", [])
    for el in p:
        saveas = el.pop("as")
        tables[saveas] = pivot(
            table=tables[el["table"]],
            using=el["using"],
            columns=el.get("columns", None),
            timestamp=el["timestamp"],
            timedelta=el.get("timedelta", None),
        )

    logger.info("Processing 'transform'.")
    t = spec.get("transform", [])
    for el in t:
        tables[el["table"]] = transform(tables[el["table"]], el["with"], el["using"])

    logger.info("Processing 'plot'.")
    p = spec.get("plot", [])
    for el in p:
        table = tables[el.pop("table")]
        if "save" in el and "as" in el["save"]:
            if patch is None:
                fp = el["save"]["as"]
            else:
                fp = el["save"]["as"].replace("$patch", patch).replace("$PATCH", patch)
            el["save"]["as"] = fp
        plot(table, **el)

    logger.info("Processing 'save'.")
    s = spec.get("save", [])
    for el in s:
        if patch is None:
            fp = el["as"]
        else:
            fp = el["as"].replace("$patch", patch).replace("$PATCH", patch)
        save(
            tables[el["table"]],
            fp,
            el.get("type"),
            el.get("columns"),
            el.get("sigma", True),
            meta,
        )
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

    version_check()
    run(args.infile, patch=args.patch)
