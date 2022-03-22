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


def columns_to_smiles(df: pd.DataFrame, prefix: Union[list[str], str]) -> dict:
    """
    Creates a dictionary with SMILES representation of all chemicals present among the
    columns of the dataframe and matched by the prefix, storing the returned
    :class:`chemicals.ChemicalMetadata` as well as the full name of the column.

    Parameters
    ----------
    df
        Source dataframe.

    prefix
        Prefix of chemical species, with species names separated by  ``->``.

    Returns
    -------
    smiles: dict
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


def load_array_data(*cols: str):
    """
    Decorator factory for data loading. Intended to load arrays.

    Creates a decorator that will load the columns specified in ``cols``
    and calls the wrapped function for each row entry.

    The load_data decorator handles the following three cases:

    - decorated function launched directly with kwargs only -> the kwargs
      that correspond to the cols listed in the decorator are converted
      to pint.Quantity

    - decorated function launched using a mixture of args and kwargs -> the
      args are assigned into kwargs using cols and converted to pint.Quantity

    - decorated function launched with pd.DataFrame and kwargs -> the cols
      specify column names in the pd.DataFrame, which are pulled out and converted
      to pint.Quantity

    Parameters
    ----------
    cols
        list of strings with the col names used to call the function

    Returns
    -------
    loading: Callable
        A wrapped version of the decorated function

    """

    def loading(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Function is called with a dataframe as the only positional argument and
            # all other parameters in kwargs:
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

                # each kwarg to get a data column specified in cols should be a string
                # create a list for each data column that should get past to the function
                raw_data = []
                # - Go through the cols array specified in the decorator.
                # - Split each col into the name of the argument and its units.
                # - Create the appropriate pint.Quantity object and place it in kwargs.
                cnames = []
                for col in cols:
                    if isinstance(col, str):
                        parts = col.split(" ")
                        cname = parts[0]
                        cnames.append(cname)
                        if len(parts) == 2:
                            cunit = parts[1][1:-1]
                        else:
                            cunit = None
                        cval = kwargs.pop(cname, None)
                        if cval is None:
                            continue
                        elif uconv:
                            raw_data.append(ureg.Quantity(df[cval].array, cunit))
                        else:
                            raw_data.append(pQ(df, cval))
                    else:
                        raise ValueError(f"Provided value for {col} is not a string")
                
                # transpose the list of pint.Quantity and iterate over it
                # so that we iterate over each timestep
                for index, row in enumerate(zip(*raw_data)):
                    # create kwargs for each data col
                    data = {col: r for col, r in zip(cnames, row)}

                    # call the function for each row in the data
                    # the function should return a dict with keys that are
                    # the names of the target columns and values that are
                    # Union[pint.Quantity, int, str]
                    retvals = func(**data, **kwargs)
                    for name, qty in retvals.items():
                        # check if the column already exists in the dataframe,
                        # if not create empty column
                        if name not in df.columns:
                            df[name] = ""
                        # fill the column and units attribute with the given values
                        if isinstance(qty, pint.Quantity):
                            df[name].iloc[index] = qty.m
                            df.attrs["units"][name] = f"{qty.u:~P}"
                        else:
                            df[name].iloc[index] = qty

            else:
                # Merge args into kwargs using cols
                if len(cols) == len(args):
                    for col, arg in zip(cols, args):
                        kwargs[col] = arg

                # Validate that all cols are pint.Quantity
                for k in cols:
                    parts = k.split(" ")
                    if len(parts) == 2:
                        cn = parts[0]
                        cu = parts[1][1:-1]
                    else:
                        cn = parts[0]
                        cu = None
                    v = kwargs.pop(k, kwargs.pop(cn, None))
                    if isinstance(v, pint.Quantity):
                        kwargs[cn] = v
                    elif isinstance(v, np.ndarray):
                        if cu is not None:
                            kwargs[cn] = ureg.Quantity(v, cu)
                        else:
                            kwargs[cn] = v
                    else:
                        raise ValueError(
                            f"The provided argument '{k}' is neither a pint.Quantity "
                            f"nor an np.ndarray: '{type(v)}'."
                        )
                return func(**kwargs)

        return wrapper

    return loading


def load_scalar_data(*cols: str):
    """
    Decorator factory for data loading. Intended to load scalars.

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
            # Function is called with a dataframe as the only positional argument and
            # all other parameters in kwargs:
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
                # - Go through the cols array specified in the decorator.
                # - Split each col into the name of the argument and its units.
                # - Create the appropriate pint.Quantity object and place it in kwargs.
                for col in cols:
                    if isinstance(col, str):
                        parts = col.split(" ")
                        cname = parts[0]
                        if len(parts) == 2:
                            cunit = parts[1][1:-1]
                        else:
                            cunit = None
                        cval = kwargs.pop(cname, None)
                        if cval is None:
                            continue
                        elif uconv:
                            kwargs[cname] = ureg.Quantity(df[cval].array, cunit)
                        else:
                            kwargs[cname] = pQ(df, cval)
                    else:
                        raise ValueError(f"Provided value for {col} is not a string")
                # Run the function. The returned object should be a
                # dict[str, Union[pint.Quantity, int, float, str]].
                # Load the results back into the dataframe.
                retvals = func(**kwargs)
                for name, qty in retvals.items():
                    if isinstance(qty, pint.Quantity):
                        df[name] = qty.m
                        if not uconv:
                            df.attrs["units"] = f"{qty.u:~P}"
                    else:
                        df[name] = qty
            # Direct call with user-supplied data.
            else:
                # Merge any args into kwargs using cols. Only works when
                # an arg is provided for each col.
                if len(cols) == len(args):
                    for col, arg in zip(cols, args):
                        kwargs[col] = arg
                # Go through cols again and convert the input data
                # into pint.Quantity, using the unit specification if necessary
                for k in cols:
                    parts = k.split(" ")
                    if len(parts) == 2:
                        cn = parts[0]
                        cu = parts[1][1:-1]
                    else:
                        cn = parts[0]
                        cu = None
                    v = kwargs.pop(k, kwargs.pop(cn, None))
                    if v is None:
                        continue
                    elif isinstance(v, pint.Quantity):
                        kwargs[cn] = v
                    elif isinstance(v, np.ndarray):
                        if cu is not None:
                            kwargs[cn] = ureg.Quantity(v, cu)
                        else:
                            kwargs[cn] = v
                    elif isinstance(v, (float, int)):
                        if cu is not None:
                            kwargs[cn] = ureg.Quantity(v, cu)
                        else:
                            kwargs[cn] = v
                    else:
                        raise ValueError(
                            f"The provided argument '{k}' is neither a pint.Quantity "
                            f"nor an np.ndarray: '{type(v)}'."
                        )
                return func(**kwargs)

        return wrapper

    return loading
