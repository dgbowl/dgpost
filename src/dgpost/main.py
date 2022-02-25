"""
Main module - execution functions for dgpost.

"""
import argparse
import logging
import os
from importlib import metadata
import pandas as pd

from dgpost.utils import parse, load, extract, transform, save


def run(path: str) -> tuple[dict, dict]:
    """
    Main API execution function.

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

    datagrams = {}
    l = spec.pop("load")
    for el in l:
        datagrams[el["as"]] = load(el["path"], el["check"])

    tables = {}
    e = spec.pop("extract")
    for el in e:
        saveas = el.pop("as")
        newdf = extract(datagrams[el.pop("from")], el)
        if saveas in tables:
            if tables[saveas].index.equals(newdf.index):
                logging.debug(
                    f"run: Concatenating columns into table '{saveas}', "
                    f"both tables have the same index."
                )
            else:
                logging.warning(
                    f"run: Concatenating columns into table '{saveas}', "
                    f"the new table has a different index!"
                )
            tables[saveas] = pd.concat([tables[saveas], newdf], axis=1)
        else:
            tables[saveas] = newdf

    t = spec.get("transform", [])
    for el in t:
        transform(tables[el["table"]], el["with"], el["using"])
    
    s = spec.get("save", [])
    for el in s:
        save(tables[el["table"]], el["as"], el.get("type"), el.get("sigma", True))
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
        "infile",
        help="File containing the YAML to be processed by dgpost.",
        default=None,
    )

    args = parser.parse_args()

    loglevel = min(max(30 - (10 * args.verbose) + (10 * args.quiet), 10), 50)
    logging.basicConfig(level=loglevel)
    logging.debug(f"loglevel set to '{logging._levelToName[loglevel]}'")

    run(args.infile)
