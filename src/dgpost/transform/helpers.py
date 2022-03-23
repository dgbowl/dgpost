"""
Module of helper functions for chemicals, elements, and unit handling.

"""
import re
import pint
import functools
import pandas as pd
import numpy as np
from uncertainties import unumpy as unp

from collections import defaultdict
from typing import Any
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
    Given a formula ``f``, return the default element for calculating
    conversion. Priority is: ``"C" > "O" > "H" > ...``.
    """
    split = re.split("(?=[A-Z]|(?<!\\d)\\d)", f)
    for el in ["C", "O", "H"]:
        if el in split:
            return el
    for s in split:
        if s.isalpha():
            return s


def columns_to_smiles(**kwargs: dict[str, Any]) -> dict:
    """
    Creates a dictionary with SMILES representation of all chemicals present among 
    the keys in the args, storing the returned :class:`chemicals.ChemicalMetadata` 
    as well as the full name within args.

    Parameters
    ----------
    args
        List of dictionaries containing

    prefix
        Prefix of chemical species, with species names separated by  ``->``.

    Returns
    -------
    smiles: dict
        A new dictionary containing the SMILES of all prefixed chemicals as keys,
        and the metadata and column specification as values.
    """
    smiles = defaultdict(dict)
    for k, v in kwargs.items():
        for kk in v.keys():
            chem = search_chemical(kk.split("->")[-1])
            smiles[chem.smiles].update({"chem": chem, k: kk})
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
    Quantity: pint.Quantity
        Unit-aware :class:`ping.Quantity` object containing the data from ``df[col]``.

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
        df.attrs["units"][tag] = f"{col.u:~P}"


def separate_data(
    data: pint.Quantity, unit: str = None
) -> tuple[np.ndarray, np.ndarray, str]:
    """
    Separates the data into values, errors and unit

    Parameters
    ----------
    data
        A :class:`pint.Quantity` object containing the data points. Can be either
        :class:`float` or :class:`uc.ufloat`.

    unit
        When specified, converts the data to this unit.

    Returns
    -------
    (values, errors, old_unit)
        Converted nominal values and errors, and the original unit of the data.
    """
    old_unit = data.u
    if not data.dimensionless and unit is not None:
        data = data.to(unit)
    data = data.m
    return unp.nominal_values(data), unp.std_devs(data), old_unit


def load_data(*cols: tuple[str, str, type]):
    """
    Decorator factory for data loading.

    Creates a decorator that will load the columns specified in ``cols``
    and calls the wrapped function for all rows at once. The function has to
    return a :class:`dict[str, pint.Quantity]`, handling an optional parameter
    ``"output"`` which prefixes (or assigns) the output data in the returned
    :class:`dict` appropriately.

    The ``load_scalar_data`` decorator handles the following cases:

    - decorated function launched directly with ``kwargs`` or with a mixture of
      ``args`` and ``kwargs``:

        - the ``args`` are assigned into ``kwargs`` using their position in the
          ``args`` and ``cols`` array listed in the decorator
        - all elements in ``kwargs`` that match the values in the ``cols`` listed
          in the decorator are converted to :class:`pint.Quantity` objects, unless
          they are one already.
        - the units for the :class:`pint.Quantity` objects are determined from the
          suffix of the ``col``

    - decorated function launched with a :class:`pd.DataFrame` as ``args`` and other
      ``kwargs``:

        - the data for ``cols`` is sourced from the :class:`pd.DataFrame`, using the
          ``kwargs`` to look for appropriate column names in the :class:`pd.DataFrame`
        - data from unit-aware :class:`pd.DataFrame` objects is loaded using the
          :func:`pQ` accessor accordingly
        - data from unit-naive :class:`pd.DataFrame` objects are coerced into
          :class:`pint.Quantity` objects using the units as specified in the ``cols``


    Parameters
    ----------
    cols
        A :class:`list[str]` containing the column names used to call the function.
        The elements in the list have to match the ``kwargs`` of the function. They
        can also be annotated by the required units, if applicable.

    Returns
    -------
    loading: Callable
        A wrapped version of the decorated function.

    """

    def loading(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # pad the cols definition to always contain "cname, cunit, ctype"
            fcols = [(list(col) + 3 * [None])[:3] for col in cols]
            
            # Function is called with a pd.DataFrame.
            # The only allowed positional argument is the pd.Dataframe, 
            # other parameters should be in kwargs:
            if len(args) > 0 and isinstance(args[0], pd.DataFrame):
                if len(args) > 1:
                    raise ValueError("Only the DataFrame should be given as argument")

                df = args[0]
                # Check if the dataframe has a units attribute. If not, the quantities
                # in the dataframe are unitless and need to be converted.
                if "units" not in df.attrs:
                    uconv = True
                else:
                    uconv = False

                data_kwargs = {}
                for cname, cunit, ctype in fcols:
                    cval = kwargs.pop(cname, None)
                    if cval is None: 
                        # cval is optional -> we want to let func use its default
                        continue
                    elif not isinstance(cval, str):
                        # cval is not a string -> convert to pint.Quantity
                        if isinstance(cval, pint.Quantity):
                            data_kwargs[cname] = cval
                        else:
                            data_kwargs[cname] = ureg.Quantity(cval, cunit)
                    elif ctype is not dict:
                        # cval is a string, and the row values (ctype) are list or scalar
                        if uconv:
                            data_kwargs[cname] = ureg.Quantity(df[cval].array, cunit)
                        else:
                            data_kwargs[cname] = pQ(df, cval)
                    else:
                        # cval is a string, but the row walues (ctype) are dict
                        # so we need to match all columns in pd.DataFrame
                        temp = {}
                        for c in df.columns:
                            if not c.startswith(cval):
                                continue
                            onlyc = c.split("->")[-1]
                            if uconv:
                                temp[onlyc] = ureg.Quantity(df[c].array, cunit)
                            else:
                                temp[onlyc] = pQ(df, c)
                        data_kwargs[cname] = temp

                # if a "list" is specified as type, we need to transpose the input:
                if list in {col[2] for col in fcols}:
                    row_k = data_kwargs.keys()
                    row_v = data_kwargs.values()
                    for i, r in enumerate(zip(*row_v)):
                        row_data = {k: v for k, v in zip(row_k, r)}
                        retvals = func(**row_data, **kwargs)
                        for name, qty in retvals.items():
                            if name not in df.columns:
                                df[name] = ""
                            if isinstance(qty, pint.Quantity):
                                qty.ito_reduced_units()
                                df[name].iloc[i] = qty.m
                                if not uconv and not qty.unitless:
                                    df.attrs["units"][name] = f"{qty.u:~P}"
                            else:
                                df[name].iloc[i] = qty
                else:
                    retvals = func(**data_kwargs, **kwargs)
                    for name, qty in retvals.items():
                        if isinstance(qty, pint.Quantity):
                            qty.ito_reduced_units()
                            df[name] = qty.m
                            if not uconv and not qty.unitless:
                                df.attrs["units"][name] = f"{qty.u:~P}"
                        else:
                            df[name] = qty
            # Direct call with user-supplied data.
            else:
                # Merge any args into kwargs using cols. Only works when
                # an arg is provided for each col.
                if len(fcols) == len(args):
                    cnames = [c[0] for c in fcols]
                    for cname, arg in zip(cnames, args):
                        kwargs[cname] = arg
                # Go through cols again and convert the input data
                # into pint.Quantity, using the unit specification if necessary
                for cname, cunit, ctype in fcols:
                    v = kwargs.pop(cname, None)
                    if v is None:
                        continue
                    elif isinstance(v, pint.Quantity):
                        kwargs[cname] = v
                    elif isinstance(v, (np.ndarray, float, int)):
                        if cunit is not None:
                            kwargs[cname] = ureg.Quantity(v, cunit)
                        else:
                            kwargs[cname] = v
                    elif isinstance(v, dict):
                        temp = {}
                        for kk, vv in v.items():
                            if isinstance(vv, pint.Quantity):
                                temp[kk] = vv
                            elif isinstance(v, (np.ndarray, float, int)):
                                if cunit is not None:
                                    temp[kk] = ureg.Quantity(vv, cunit)
                                else:
                                    temp[kk] = vv
                        kwargs[cname] = temp
                    else:
                        raise ValueError(
                            f"The provided argument '{cname}' is neither a pint.Quantity "
                            f"nor an np.ndarray: '{type(v)}'."
                        )
                return func(**kwargs)

        return wrapper

    return loading
