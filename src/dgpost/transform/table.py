"""
**table**: utilities for operations with tables
-----------------------------------------------

Provides convenience functions for operating with tables, including
:func:`~dgpost.transform.table.combine_namespaces` for combining ``->``-separated
namespaces of values or chemicals into a single namespace; and
:func:`~dgpost.transform.table.combine_columns` for combining individual columns
into a single column.

.. codeauthor:: 
    Peter Kraus

"""
import pint
import pandas as pd
from dgpost.utils.helpers import load_data, columns_to_smiles
from collections import defaultdict
from typing import Iterable
from yadg.dgutils import ureg


@load_data(
    ("a", None, dict),
    ("b", None, dict),
)
def combine_namespaces(
    a: dict[str, pint.Quantity],
    b: dict[str, pint.Quantity],
    conflicts: str = "sum",
    output: str = "c",
    fillnan: bool = True,
    chemicals: bool = False,
) -> dict[str, pint.Quantity]:
    """
    Combines two namespaces into one. Unit checks are performed, with the resulting
    units corresponding to the units in namespace ``a``. By default, the output
    namespace is called ``"c"``. Optionally, the keys in each namespace can be treated
    as chemicals.

    Parameters
    ----------
    a
        Namespace ``a``.

    b
        Namespace ``b``.

    conflicts
        Name resolution scheme. Can be either ``"sum"`` where conflicts are summed,
        or ``"replace"``, where conflicting values in ``a`` are overwritten by ``b``.

    fillnan
        Toggle whether ``NaN`` values within the columns ought to be treated as
        zeroes or as ``NaN``. Default is ``True``.

    chemicals
        Treat keys within ``a`` and ``b`` as chemicals, and combine them accordingly.
        Default is ``False``.

    output
        Namespace of the returned dictionary. By default ``"c"``.

    """
    ret = {}
    u = a[next(iter(a))].u

    if chemicals:
        names = columns_to_smiles(a=a, b=b)
    else:
        names = defaultdict(dict)
        for k in a.keys():
            names[k].update({"a": k})
        for k in b.keys():
            names[k].update({"b": k})

    for k, v in names.items():
        if "a" in v and "b" in v:
            aa = a[v["a"]]
            bb = b[v["b"]]
            if fillnan:
                if isinstance(aa.m, Iterable) and isinstance(bb.m, Iterable):
                    aa.m[pd.isna(aa.m)] = 0
                    bb.m[pd.isna(bb.m)] = 0
                else:
                    aa = ureg.Quantity(0, aa.u) if pd.isna(aa.m) else aa
                    bb = ureg.Quantity(0, bb.u) if pd.isna(bb.m) else bb

            if conflicts == "sum":
                ret[v["a"]] = aa + bb
            elif conflicts == "replace":
                ret[v["a"]] = bb.to(u)
            else:
                raise ValueError(f"Unknown value of 'conflicts': {conflicts}")
        elif "a" in v:
            ret[v["a"]] = a[v["a"]]
        elif "b" in v:
            ret[v["b"]] = b[v["b"]].to(u)

    out = {}
    for k, v in ret.items():
        out[f"{output}->{k}"] = v

    return out


@load_data(
    ("a", None),
    ("b", None),
)
def combine_columns(
    a: pint.Quantity,
    b: pint.Quantity,
    fillnan: bool = True,
    output: str = "c",
) -> dict[str, pint.Quantity]:
    """
    Combines two columns into one. Unit checks are performed, with the resulting
    units corresponding to the units in column ``a``. By default, the output
    namespace is called ``"c"``.

    Parameters
    ----------
    a
        Column ``a``.

    b
        Column ``b``.

    fillnan
        Toggle whether ``NaN`` values within the columns ought to be treated as
        zeroes or as ``NaN``. Default is ``True``.

    output
        Namespace of the returned dictionary. By default ``"c"``.

    """
    if fillnan:
        if isinstance(a.m, Iterable) and isinstance(b.m, Iterable):
            a.m[pd.isna(a.m)] = 0
            b.m[pd.isna(b.m)] = 0
        else:
            a = ureg.Quantity(0, a.u) if pd.isna(a.m) else a
            b = ureg.Quantity(0, b.u) if pd.isna(b.m) else b
    ret = a + b
    return {output: ret}
