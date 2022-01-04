"""
Module of helper functions for chemicals and elements.

"""
import re
import pandas as pd

from collections import defaultdict
from typing import Union
from chemicals.identifiers import search_chemical


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
