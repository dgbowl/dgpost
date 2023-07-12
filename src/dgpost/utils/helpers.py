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
from inspect import signature

from collections import defaultdict
from typing import Any, Union, Sequence
from chemicals.elements import periodic_table, simple_formula_parser
from chemicals.identifiers import search_chemical
import logging

logger = logging.getLogger(__name__)
ureg = pint.get_application_registry()

ureg.define("refractive_index_units = [] = RIU")
ureg.define("standard_milliliter = milliliter = smL")


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


def pQ(
    df: pd.DataFrame, col: Union[str, tuple[str]], unit: str = None
) -> ureg.Quantity:
    """
    Unit-aware dataframe accessor function.

    Given a dataframe in ``df`` and a column name in ``col``, the function looks
    through the units stored in ``df.attrs["units"]`` and returns a unit-annotated
    :class:`ureg.Quantity` containing the column data. Alternatively, the data in
    ``df[col]`` can be annotated by the provided ``unit``.

    .. note::

        If ``df.attrs`` has no units, or ``col`` is not in ``df.attrs["units"]``,
        the returned :class:`ureg.Quantity` is dimensionless.

    Parameters
    ----------
    df
        A :class:`pd.DataFrame`, optionally annotated with units in ``df.attrs``.

    col
        The :class:`str` name of the column to be loaded from the ``df``.

    unit
        Optional override for units.

    Returns
    -------
    Quantity: ureg.Quantity
        Unit-aware :class:`ping.Quantity` object containing the data from ``df[col]``.

    """
    if df.columns.nlevels == 1:
        vals = df[col].array
    elif isinstance(col, tuple) and len(col) == df.columns.nlevels:
        vals = df[col].array
    else:
        vals = df[col].squeeze().array
    if unit is not None:
        pass
    else:
        unit = get_units(col, df)
    try:
        q = ureg.Quantity(vals, unit)
    except pint.errors.UndefinedUnitError:
        logger.warning(
            f"pint does not understand unit '{unit}', "
            "treating Quantity as dimensionless"
        )
        ureg.define(f"{unit} = []")
        q = ureg.Quantity(vals, unit)
    return q


def separate_data(
    data: pint.Quantity, unit: str = None
) -> tuple[np.ndarray, np.ndarray, str]:
    """
    Separates the data into values, errors and units

    Parameters
    ----------
    data
        A :class:`ureg.Quantity` object containing the data points. Can be either
        :class:`float` or :class:`uc.ufloat`.

    unit
        When specified, converts the data to this unit.

    Returns
    -------
    (values, errors, old_unit)
        Converted nominal values and errors, and the original unit of the data.
    """
    old_unit = data.u
    if unit is not None and not data.dimensionless:
        data = data.to(unit)
    data = data.m
    return unp.nominal_values(data), unp.std_devs(data), old_unit


def load_data(*cols: tuple[str, str, type]):
    """
    Decorator factory for data loading.

    Creates a decorator that will load the columns specified in ``cols``
    and calls the wrapped function ``func`` as appropriate. The ``func`` has to
    accept :class:`ureg.Quantity` objects, return a :class:`dict[str, ureg.Quantity]`,
    and handle an optional parameter ``"output"`` which prefixes (or assigns) the
    output data in the returned :class:`dict` appropriately.

    The argument of the decorator is a :class:`list[tuple]`, with each element being
    a are :class:`tuple[str, str, type]`. The first field in this :class:`tuple` is
    the :class:`str` name of the argument of the decorated ``func``, the second
    :class:`str` field denotes the default units for that argument (or ``None`` for
    a unitless quantity), and the :class:`type` field allows the use of the decorator
    with functions that expect :class:`list` of points in the argument (such as
    trace-processing functions) or :class:`dict` of :class:`ureg.Quantity` objects
    (such as functions operating on chemical compositions).

    The decorator handles the following cases:

    - the decorated ``func`` is launched directly, either with ``kwargs`` or with a
      mixture of ``args`` and ``kwargs``:

        - the ``args`` are assigned into ``kwargs`` using their position in the
          ``args`` and ``cols`` array as provided to the decorator
        - all elements in ``kwargs`` that match the argument names in the ``cols``
          :class:`list` provided to the decorator are converted to
          :class:`ureg.Quantity` objects, assigning the default units using the
          data from the ``cols`` :class:`list`, unless they are a
          :class:`ureg.Quantity` already.

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
          :class:`ureg.Quantity` objects using the default units as specified in the
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
                df = arrow_to_multiindex(args[0], warn=True)
                # Check if the dataframe has a units attribute. If not, the quantities
                # in the dataframe are unitless and need to be converted.
                if "units" in df.attrs:
                    uconv = False
                else:
                    uconv = True

                # keep original kwargs cname-cval keypairs in orig_kwargs
                orig_kwargs = {}
                data_kwargs = {}
                for cname, cunit, ctype in fcols:
                    cval = kwargs.pop(cname, None)
                    orig_kwargs[cname] = cval
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
                        keys = keys_in_df(cval, df)
                        if len(keys) > 1:
                            raise RuntimeError(
                                f"multiple columns in DataFrame matched with '{cval=}':"
                                f"{keys=}"
                            )
                        elif len(keys) == 0:
                            q = ureg.Quantity(cval)
                            if q.dimensionless:
                                q = q * ureg(cunit)
                            data_kwargs[cname] = q
                        else:
                            key = keys.pop()
                            if uconv:
                                data_kwargs[cname] = pQ(df, key, unit=cunit)
                            else:
                                data_kwargs[cname] = pQ(df, key)
                    else:
                        # cval is a string, but the row walues (ctype) are dict
                        # so we need to match all columns in pd.DataFrame
                        ctup = key_to_tuple(cval)
                        keys = keys_in_df(cval, df)
                        temp = {}
                        for key in keys:
                            if len(key) > len(ctup) + 1:
                                raise RuntimeError(
                                    f"DataFrame column '{key=}' matches column "
                                    f"specification '{cval=}', but cannot be "
                                    f"coerced into a dict."
                                )
                            c = key[-1]
                            if uconv:
                                temp[c] = pQ(df, key, unit=cunit)
                            else:
                                temp[c] = pQ(df, key)
                        data_kwargs[cname] = temp

                # if the called function requires the names of columns,
                # it can ask for them by having _inp in its signature
                if "_inp" in signature(func).parameters:
                    kwargs["_inp"] = orig_kwargs

                units = {}
                # if a "list" is specified as type, we need to transpose the input:
                if list in {col[2] for col in fcols}:
                    if all([col[2] is list for col in fcols]):
                        row_k = data_kwargs.keys()
                        row_v = data_kwargs.values()
                    else:
                        row_k = []
                        row_v = []
                        to_pad = []
                        for k, v in data_kwargs.items():
                            for col in fcols:
                                if k == col[0] and col[2] is list:
                                    row_k.append(k)
                                    row_v.append(v)
                                elif k == col[0] and col[2] is None:
                                    row_k.append(k)
                                    row_v.append([v])
                                    to_pad.append(len(row_k) - 1)
                        l = max([len(i) for i in row_v])
                        for i in to_pad:
                            row_v[i] = row_v[i] * l
                    ret_data = {}
                    for ri, r in enumerate(zip(*row_v)):
                        row_data = {k: v for k, v in zip(row_k, r)}
                        retvals = func(**row_data, **kwargs)
                        for name, qty in retvals.items():
                            if name not in ret_data:
                                ret_data[name] = [None] * ri
                            if isinstance(qty, pint.Quantity):
                                qty.ito_reduced_units()
                                ret_data[name].append(qty.m)
                                if not uconv and not qty.unitless:
                                    units[name] = f"{qty.u:~P}"
                            else:
                                ret_data[name].append(qty)
                        for name in ret_data.keys():
                            if name not in retvals:
                                ret_data[name].append(None)
                else:
                    retvals = func(**data_kwargs, **kwargs)
                    ret_data = {}
                    for name, qty in retvals.items():
                        if isinstance(qty, pint.Quantity):
                            qty.ito_reduced_units()
                            ret_data[name] = qty.m
                            if not uconv and not qty.unitless:
                                units[name] = f"{qty.u:~P}"
                        else:
                            ret_data[name] = qty
                ddf = arrow_to_multiindex(
                    pd.DataFrame(ret_data, index=df.index),
                    warn=False,
                )
                newdf = combine_tables(df, ddf)
                if "units" in df.attrs:
                    newdf.attrs["units"] = df.attrs["units"]
                    for k, v in units.items():
                        set_units(k.split("->"), v, newdf)
                return newdf

            # Direct call with user-supplied data.
            else:
                # Merge any args into kwargs using cols. Only works when
                # an arg is provided for each col.
                if len(fcols) == len(args):
                    cnames = [c[0] for c in fcols]
                    for cname, arg in zip(cnames, args):
                        kwargs[cname] = arg
                # Go through cols again and convert the input data
                # into ureg.Quantity, using the unit specification if necessary
                for cname, cunit, ctype in fcols:
                    v = kwargs.pop(cname, None)
                    if v is None:
                        continue
                    elif isinstance(v, pint.Quantity):
                        kwargs[cname] = v
                    elif isinstance(v, (pd.Series, np.ndarray, float, int, list)):
                        if isinstance(v, pd.Series):
                            v = v.values
                        if cunit is not None:
                            kwargs[cname] = ureg.Quantity(v, cunit)
                        else:
                            kwargs[cname] = v
                    elif isinstance(v, dict):
                        temp = {}
                        for kk, vv in v.items():
                            if isinstance(vv, pint.Quantity):
                                temp[kk] = vv
                            elif isinstance(
                                vv, (pd.Series, np.ndarray, float, int, list)
                            ):
                                if isinstance(vv, pd.Series):
                                    vv = vv.values
                                if cunit is not None:
                                    temp[kk] = ureg.Quantity(vv, cunit)
                                else:
                                    temp[kk] = vv
                        kwargs[cname] = temp
                    else:
                        raise ValueError(
                            f"The provided argument '{cname}' is neither a ureg.Quantity "
                            f"nor an np.ndarray: '{type(v)}'."
                        )
                return func(**kwargs)

        return wrapper

    return loading


def combine_tables(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    """
    Combine two :class:`pd.DataFrames` into a new :class:`pd.DataFrame`.

    Assumes the :class:`pd.DataFrames` contain a :class:`pd.MultiIndex`. Automatically
    pads the :class:`pd.MultiIndex` to match the higher number of levels, if necessary.
    Merges units.

    """
    if len(a.columns) == 0:
        temp = b
    elif a.columns.nlevels == b.columns.nlevels:
        for k in a.columns:
            if k in b.columns:
                del a[k]
        temp = a.join(b, how="outer")
    else:
        if a.columns.nlevels > b.columns.nlevels:
            l = a
            r = b
        else:
            l = b
            r = a
        llen = l.columns.nlevels
        rcols = []
        for col in r.columns:
            rcols.append(tuple(list(col) + [None] * (llen - len(col))))
        r.columns = pd.MultiIndex.from_tuples(rcols)
        for k in l.columns:
            if k in r.columns:
                del l[k]
        temp = l.join(r, how="outer")
    temp.attrs = a.attrs
    if "units" in b.attrs:
        if "units" not in temp.attrs:
            temp.attrs["units"] = {}
        temp.attrs["units"].update(b.attrs.get("units", {}))
    return temp


def arrow_to_multiindex(df: pd.DataFrame, warn: bool = True) -> pd.DataFrame:
    """
    Convert the provided :class:`pd.DataFrame` to a ``dgpost``-compatible format.

    - converts tables with :class:`pd.Index` into :class:`pd.MultiIndex`,
    - converts ``->``-separated namespaces into :class:`pd.MultiIndex`,
    - processes units into nested :class:`dicts`.

    """
    cols = []
    oldunits = []
    d = 1
    for oldcol in df.columns:
        if "->" in oldcol:
            if warn:
                logger.warning(
                    "Loading table with namespaces stored using old '->' syntax. "
                    "Consider updating your table to a MultiIndexed one."
                )
                warn = False
            parts = oldcol.split("->")
            d = max(d, len(parts))
        elif isinstance(oldcol, tuple):
            parts = list(oldcol)
        elif isinstance(oldcol, list):
            parts = oldcol
        elif isinstance(oldcol, str):
            parts = [oldcol]
        else:
            raise RuntimeError(f"column '{oldcol=}' is a '{type(oldcol)=}'")
        cols.append(parts)
        if "units" in df.attrs:
            oldunits.append(get_units(oldcol, df))
    units = {}
    for i, tup in enumerate(zip(cols, oldunits)):
        col, unit = tup
        if len(col) < d:
            cols[i] = col + [None] * (d - len(col))
        col = tuple(col)
        cols[i] = col
        set_units(col, unit, units)
    if "units" in df.attrs:
        df.attrs["units"] = units
    if len(cols) > 0:
        df.columns = pd.MultiIndex.from_tuples(cols)
    return df.sort_index()


def keys_in_df(key: Union[str, tuple], df: pd.DataFrame) -> set[tuple]:
    """
    Find all columns in the provided :class:`pd.DataFrame` that match ``key``.

    Returns a :class:`set` of all columns in the ``df`` which are matched by ``key``.
    Assumes the provided :class:`pd.DataFrame` contains a :class:`pd.MultiIndex`.

    """
    key = key_to_tuple(key)
    t = df.sort_index(axis=1)
    keys = set()
    for col in t.columns:
        if col[: len(key)] == key:
            keys.add(col)
    return keys


def key_to_tuple(key: Union[str, tuple]) -> tuple:
    """
    Convert a provided ``key`` to a :class:`tuple` for use with :class:`pd.DataFrames`
    containing a :class:`pd.MultiIndex`.

    """
    if isinstance(key, str):
        if "->" in key:
            key = key.split("->")
            if key[-1] == "*":
                key = key[:-1]
        else:
            key = [key]
        key = tuple(key)
    elif isinstance(key, tuple):
        pass
    else:
        raise RuntimeError(f"passed '{key=}' is '{type(key)=}'")
    return key


def get_units(
    key: Union[str, Sequence],
    df: pd.DataFrame,
) -> Union[str, None]:
    """
    Given a ``key`` corresponding to a column in the ``df``, return the units. The
    provided ``key`` can be both a :class:`str` for ``df`` with :class:`pd.Index`,
    or any other :class:`Sequence` for a ``df`` with :class:`pd.MultiIndex`.

    """

    def recurse(key: Union[str, Sequence], units: dict) -> Union[str, None]:
        if isinstance(key, str):
            return units.get(key, None)
        elif isinstance(key, Sequence):
            if len(key) == 1:
                return recurse(key[0], units)
            elif key[0] in units:
                return recurse(key[1:], units[key[0]])
            else:
                return None

    if not isinstance(key, str):
        key = [k for k in key if isinstance(k, str)]
    return recurse(key, df.attrs.get("units", {}))


def set_units(
    key: Union[str, Sequence],
    unit: Union[str, None],
    target: Union[dict, pd.DataFrame],
) -> None:
    """
    Set the units of ``key`` to ``unit`` in the ``target`` object, which can be
    either a :class:`dict` or a :class:`pd.DataFrame`. See also :func:`get_units`.

    """

    def recurse(key: Union[str, Sequence], unit: str, target: dict) -> None:
        if isinstance(key, str):
            target[key] = unit
        elif isinstance(key, Sequence):
            if len(key) == 1:
                recurse(key[0], unit, target)
            else:
                if key[0] not in target:
                    target[key[0]] = {}
                recurse(key[1:], unit, target[key[0]])

    if not isinstance(key, str):
        key = [k for k in key if isinstance(k, str)]
    if unit is None:
        return
    if isinstance(target, pd.DataFrame):
        recurse(key, unit, target.attrs["units"])
    else:
        recurse(key, unit, target)
