"""
Module of helper functions for chemicals, elements, and unit handling.

"""
import re
import pint
import pandas as pd

from collections import defaultdict
from typing import Union
from chemicals.identifiers import search_chemical
from yadg.dgutils import ureg


def element_from_formula(f: str, el: str) -> int:
    """
    Given a formula ``f``, return the number of atoms of element ``el`` in that formula.
    """
    split = re.split("(?=[A-Z]|(?<!\\d)\\d)", f)
    if el not in split:
        return 0
    else:
        i = split.index(el)
        if i == len(split) - 1:
            return 1
        elif split[i + 1].isnumeric():
            return int(split[i + 1])
        else:
            return 1


def default_element(f: str) -> str:
    """
    Given a formula ``f``, return the default element for conversion. Priority is:
    ``"C" > "O" > "H" > ...``.
    """
    split = re.split("(?=[A-Z]|(?<!\\d)\\d)", f)
    for el in ["C", "O", "H"]:
        if el in split:
            return el
    for s in split:
        if s.isalpha():
            return s


def columns_to_smiles(df: pd.DataFrame, prefix: Union[list[str], str]) -> dict:
    """
    Creates a dictionary with SMILES representation of all chemicals, in the dataframe
    matched by the prefix, storing the returned :class:`chemicals.ChemicalMetadata` as
    well as the full name of the column.

    Parameters
    ----------
    df
        Source dataframe.

    prefix
        Prefix of chemical species, with species names separated by  ``->``.

    Returns
    -------
    :class:`dict`
        A new dictionary containing the SMILES of all prefixed chemicals as keys,
        and the metadata and column specification as values.
    """
    smiles = defaultdict(dict)
    if isinstance(prefix, str):
        prefix = [prefix]
    for col in df.columns:
        for p in prefix:
            if col.startswith(p):
                chem = search_chemical(col.split("->")[1])
                smiles[chem.smiles].update({"chem": chem, p: col})
    return smiles


def pQ(df: pd.DataFrame, col: str) -> pint.Quantity:
    """
    Unit-aware dataframe accessor function.

    Given a dataframe in ``df`` and a column name in ``col``, the function looks
    through the units stored in ``df.attrs["units"]`` and returns a unit-annotated
    :class:`pint.Quantity` containing the column data.

    .. note::
        If ``df.attrs`` has no units, or ``col`` is not in ``df.attrs["units"]``,
        the returned :class:`pint.Quantity` is dimensionless.

    Parameters
    ----------
    df
        Pandas dataframe, optionally annotated with units.

    col
        Column from the dataframe.

    Returns
    -------
    :class:`pint.Quantity`
        Unit-aware numpy-like object containing the data from ``df[col]``.

    """
    vals = df[col].array
    unit = df.attrs.get("units", {}).get(col, "")
    return ureg.Quantity(vals, unit)


def save(df: pd.DataFrame, tag: str, col: pint.Quantity) -> None:
    """
    Unit aware dataframe storing function.

    Given a dataframe in ``df``, and the new column header in ``tag`` and the data
    in ``col``, this function stores the data portion of ``col`` in the dataframe
    as ``df[tag]``, and annotates the dataframe with the units.

    If the units of ``col`` are dimensionless, the unit is not stored.

    Parameters
    ----------
    df
        Pandas dataframe, optionally annotated with units.

    tag
        Name of the new column.

    col
        Data of the new column.

    """
    col.ito_base_units()
    df[tag] = col.m
    if not col.dimensionless:
        if "units" not in df.attrs:
            df.attrs["units"] = {}
        df.attrs["units"][tag] = str(col.u)


# pd.to_pickle(df, f"C:\\Users\\krpe\\postprocess\\tests\\{outpath}")
