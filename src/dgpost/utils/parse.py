"""
`parse`: YAML processing schema and loader/parser function.
"""
import strictyaml as sy
import os
from .schema import schema


def parse_yaml(fn: str) -> dict:
    """
    Loads the yaml file in ``fn``, parses it according to the schema, and returns
    the resulting specification dictionary.

    Parameters
    ----------
    fn
        Path to the yaml file to load.

    Returns
    -------
    dict
        The parsed job specification as a dictionary.

    """
    with open(fn, "r") as infile:
        yaml = infile.read()

    return sy.load(yaml, schema).data


def parse(fn: str) -> dict:
    """
    Input file parsing function.

    Currently, only yaml files are supported, hence this function is a wrapper around
    :func:`parse_yaml`.

    """
    assert os.path.exists(fn) and os.path.isfile(fn), (
        f"parse: provided file namen '{fn}' does not exist " f"or is not a valid file"
    )

    return parse_yaml(fn)
