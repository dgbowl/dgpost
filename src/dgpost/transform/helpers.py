"""
**helpers**: helper functions for the :mod:`~dgpost.transform` package
----------------------------------------------------------------------
.. codeauthor:: 
    Peter Kraus,
    Ueli Sauter

"""

import pint
import functools
import pandas as pd
import numpy as np
from uncertainties import unumpy as unp
from rdkit import Chem

from collections import defaultdict
from typing import Any
from chemicals.elements import periodic_table, simple_formula_parser
from chemicals.identifiers import search_chemical
from yadg.dgutils import ureg


def element_from_formula(f: str, el: str) -> int:
    """
    Given a chemical formula ``f``, returns the number of atoms of element ``el``
    in that formula.

    """
    elements = simple_formula_parser(f)
    if el not in elements:
        return 0
    else:
        return elements[el]


def default_element(f: str) -> str:
    """
    Given a formula ``f``, return the default element for calculating
    conversion. The priority list is ``["C", "O", "H"]``.
    """
    elements = simple_formula_parser(f)
    for el in ["C", "O", "H"]:
        if el in elements:
            return el
    return elements.keys()[0]


def name_to_chem(name: str) -> str:
    exceptions = {"CO": "carbon monoxide"}
    if name in exceptions.keys():
        query = exceptions[name]
    else:
        query = name
    return search_chemical(query)


def columns_to_smiles(**kwargs: dict[str, dict[str, Any]]) -> dict:
    """
    Creates a dictionary with a SMILES representation of all chemicals present among
    the keys in the kwargs, storing the returned :class:`chemicals.ChemicalMetadata`
    as well as the full name within args.

    Parameters
    ----------
    kwargs
        A :class:`dict` containing :class:`dict[str, Any]` values. The :class:`str`
        keys of the inner :class:`dicts` are parsed to SMILES.

    Returns
    -------
    smiles: dict
        A new :class:`dict[str, dict]` containing the SMILES of all prefixed chemicals
        as :class:`str` keys, and the metadata and column specification as the
        :class:`dict` values.

    """
    ret = defaultdict(dict)
    for k, v in kwargs.items():
        for kk in v.keys():
            name = kk.split("->")[-1]
            chem = name_to_chem(name)
            ret[chem.smiles].update({"chem": chem, k: kk})
    return ret


def electrons_from_smiles(
    smiles: str,
    ions: dict = None,
) -> float:
    charges = defaultdict(lambda: 0)
    charges.update(ions)
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    n = 0
    for atom in mol.GetAtoms():
        ela = periodic_table[atom.GetAtomicNum()].elneg
        for bond in atom.GetBonds():
            btom = bond.GetOtherAtom(atom)
            elb = periodic_table[btom.GetAtomicNum()].elneg
            bmul = bond.GetBondTypeAsDouble()
            if ela > elb:
                n -= bmul
            elif ela < elb:
                n += bmul
        n += charges[atom.GetSymbol()]
    return float(n)


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
        A :class:`pd.DataFrame`, optionally annotated with units in ``df.attrs``.

    col
        The :class:`str` name of the column to be loaded from the ``df``.

    Returns
    -------
    Quantity: pint.Quantity
        Unit-aware :class:`ping.Quantity` object containing the data from ``df[col]``.

    """
    vals = df[col].array
    unit = df.attrs.get("units", {}).get(col, "")
    return ureg.Quantity(vals, unit)


def separate_data(
    data: pint.Quantity, unit: str = None
) -> tuple[np.ndarray, np.ndarray, str]:
    """
    Separates the data into values, errors and units

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
    and calls the wrapped function ``func`` as appropriate. The ``func`` has to
    accept :class:`pint.Quantity` objects, return a :class:`dict[str, pint.Quantity]`,
    and handle an optional parameter ``"output"`` which prefixes (or assigns) the
    output data in the returned :class:`dict` appropriately.

    The argument of the decorator is a :class:`list[tuple]`, with each element being
    a are :class:`tuple[str, str, type]`. The first field in this :class:`tuple` is
    the :class:`str` name of the argument of the decorated ``func``, the second
    :class:`str` field denotes the default units for that argument (or ``None`` for
    a unitless quantity), and the :class:`type` field allows the use of the decorator
    with functions that expect :class:`list` of points in the argument (such as
    trace-processing functions) or :class:`dict` of :class:`pint.Quantity` objects
    (such as functions operating on chemical compositions).

    The decorator handles the following cases:

    - the decorated ``func`` is launched directly, either with ``kwargs`` or with a
      mixture of ``args`` and ``kwargs``:

        - the ``args`` are assigned into ``kwargs`` using their position in the
          ``args`` and ``cols`` array as provided to the decorator
        - all elements in ``kwargs`` that match the argument names in the ``cols``
          :class:`list` provided to the decorator are converted to
          :class:`pint.Quantity` objects, assigning the default units using the
          data from the ``cols`` :class:`list`, unless they are a
          :class:`pint.Quantity` already.

    - decorated ``func`` is launched with a :class:`pd.DataFrame` as the ``args``
      and other parameters in ``kwargs``:

        - the data for the arguments listed in ``cols`` is sourced from the columns
          of the :class:`pd.DataFrame`, using the provided :class:`str` arguments to
          find the appropriate columns
        - if :class:`pd.Index` is provided as the data type, and no column name is
          provided by the user, the index of the :class:`pd.DataFrame` is passed
          into the called function
        - data from unit-aware :class:`pd.DataFrame` objects is loaded using the
          :func:`pQ` accessor accordingly
        - data from unit-naive :class:`pd.DataFrame` objects are coerced into
          :class:`pint.Quantity` objects using the default units as specified in the
          ``cols`` :class:`list`

    Parameters
    ----------
    cols
        A :class:`list[tuple[str, str, type]]` containing the column names used to
        call the ``func``.

    Returns
    -------
    loading: Callable
        A wrapped version of the decorated ``func``.

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
                    if ctype is pd.Index and cval is None:
                        # if ctype is pd.Index, it can still be overriden by cval
                        # otherwise send the df.index wrapped in cunit
                        data_kwargs[cname] = ureg.Quantity(df.index, cunit)
                    elif cval is None:
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
                        print(f"{name=}")
                        print(f"{qty=}")
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
                    elif isinstance(v, (np.ndarray, float, int, list)):
                        if cunit is not None:
                            kwargs[cname] = ureg.Quantity(v, cunit)
                        else:
                            kwargs[cname] = v
                    elif isinstance(v, dict):
                        temp = {}
                        for kk, vv in v.items():
                            if isinstance(vv, pint.Quantity):
                                temp[kk] = vv
                            elif isinstance(vv, (np.ndarray, float, int, list)):
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
