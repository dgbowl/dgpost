"""
.. codeauthor::
    Peter Kraus

Provides convenience functions for operating with tables, including
:func:`~dgpost.transform.table.combine_namespaces` for combining ``->``-separated
namespaces of values or chemicals into a single namespace;
:func:`~dgpost.transform.table.combine_columns` for combining individual columns
into a single column; :func:`~dgpost.transform.table.set_uncertainty` for
stripping or replacing uncertainties from data, and :func:`~dgpost.transform.table.apply_linear`
and :func:`~dgpost.transform.table.apply_inverse` for applying linear corrections to
columns or namespaces.

.. rubric:: Functions

.. autosummary::

    combine_namespaces
    combine_columns
    set_uncertainty
    apply_linear
    apply_inverse


"""

import pint
import pandas as pd
import numpy as np
from dgpost.utils.helpers import load_data, separate_data, columns_to_smiles
from collections import defaultdict
from typing import Iterable, Union
from uncertainties import UFloat, unumpy as unp

ureg = pint.get_application_registry()


@load_data(
    ("a", None, dict),
    ("b", None, dict),
)
def combine_namespaces(
    a: dict[str, pint.Quantity],
    b: dict[str, pint.Quantity],
    conflicts: str = "sum",
    output: str = None,
    fillnan: bool = True,
    chemicals: bool = False,
    _inp: dict = {},
) -> dict[str, pint.Quantity]:
    """
    Combines two namespaces into one. Unit checks are performed, with the resulting
    units corresponding to the units in namespace ``a``. By default, the output
    namespace is set to ``a``. Optionally, the keys in each namespace can be treated
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
        Namespace of the returned dictionary. Defaults to the namespace of ``a``.

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

    if output is None:
        output = _inp.get("a", "c")

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
    output: str = None,
    _inp: dict = {},
) -> dict[str, pint.Quantity]:
    """
    Combines two columns into one. Unit checks are performed, with the resulting
    units corresponding to the units in column ``a``. By default, the output
    column is set to ``a``.

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
        Namespace of the returned dictionary. By defaults to the name of column ``a``.

    """

    def fillnans(vals):
        mags = vals.m
        if isinstance(mags, float):
            return ureg.Quantity(0, vals.u) if pd.isna(mags) else vals
        elif isinstance(mags, UFloat):
            return ureg.Quantity(0, vals.u) if pd.isna(mags.n) else vals
        else:
            nans = pd.isna(unp.nominal_values(mags))
            vals[nans] = ureg.Quantity(0, vals.u)
            return vals

    if fillnan:
        a = fillnans(a)
        b = fillnans(b)
    ret = a + b

    if output is None:
        output = _inp.get("a", "c")
    return {output: ret}


@load_data(
    ("namespace", None, dict),
    ("column", None),
)
def set_uncertainty(
    namespace: dict[str, pint.Quantity] = None,
    column: pint.Quantity = None,
    abs: Union[pint.Quantity, float] = None,
    rel: Union[pint.Quantity, float] = None,
    _inp: dict = {},
) -> dict[str, pint.Quantity]:
    """
    Allows for stripping or replacing uncertainties using absolute and relative
    values. Can target either namespaces, or individual columns. If both ``abs``
    and ``rel`` uncertainty is provided, the higher of the two values is set.
    If neither ``abs`` nor ``rel`` are provided, the uncertainties are stripped.

    Parameters
    ----------
    namespace
        The prefix of the namespace for which uncertainties are to be replaced or
        stripped. Cannot be supplied along with ``column``.

    column
        The name of the column for which uncertainties are to be replaced or stripped.
        Cannot be supplied along with ``namespace``

    abs
        The absolute value of the uncertainty. If units are not supplied, the units of
        the column/namespace will be used. If both ``abs`` and ``rel`` are ``None``,
        the existing uncertainties will be stripped.

    rel
        The relative value of the uncertainty, should be in dimensionless units. If
        both ``abs`` and ``rel`` are ``None``, the existing uncertainties will be stripped.

    """
    assert (namespace is not None and column is None) or (
        namespace is None and column is not None
    )

    outk = []
    outv = []
    outs = []
    outu = []

    if column is not None:
        v, s, u = separate_data(column)
        outk.append(_inp.get("column", "output"))
        outv.append(v)
        outs.append(s)
        outu.append(u)
    elif namespace is not None:
        for key, vals in namespace.items():
            v, s, u = separate_data(vals)
            outk.append(_inp.get("namespace", "output") + f"->{key}")
            outv.append(v)
            outs.append(s)
            outu.append(u)
    ret = {}
    for k, v, s, u in zip(outk, outv, outs, outu):
        if abs is None and rel is None:
            ret[k] = ureg.Quantity(v, u)
        else:
            if isinstance(abs, float):
                abs = ureg.Quantity(abs, u)
            if isinstance(rel, float):
                rel = ureg.Quantity(rel, "dimensionless")
            if rel is None:
                s = abs.to(u).m
            elif abs is None:
                s = np.abs(v) * rel.to("dimensionless").m
            else:
                s = np.maximum(abs.to(u).m, np.abs(v) * rel.to("dimensionless").m)
            ret[k] = ureg.Quantity(unp.uarray(v, s), u)
    return ret


@load_data(
    ("namespace", None, dict),
    ("column", None),
)
def apply_linear(
    namespace: dict[str, pint.Quantity] = None,
    column: pint.Quantity = None,
    slope: Union[pint.Quantity, float] = None,
    intercept: Union[pint.Quantity, float] = None,
    output: str = "output",
    _inp: dict = {},
) -> dict[str, pint.Quantity]:
    """
    Allows for applying linear functions / corrections to columns and namespaces.

    Given the linear formula, :math:`y = m \\times x + c`, this function returns :math:`y`
    calculated from the input, where :math:`m` is the provided ``slope`` and :math:`c`
    is the provided ``intercept``.

    The arguments ``slope`` and ``intercept`` can be provided without units, in which
    case the units of ``column`` or ``namespace`` are preserved. If units of ``slope``
    and ``intercept``  are provided, they have to be dimensionally consistent.

    The arguments ``slope`` and ``intercept`` can be provided with uncertainties, in
    which case the uncertainty of the output value is calculated from linear uncertainty
    propagation.

    Parameters
    ----------
    namespace
        The prefix of the namespace for which uncertainties are to be replaced or
        stripped. Cannot be supplied along with ``column``.

    column
        The name of the column for which uncertainties are to be replaced or stripped.
        Cannot be supplied along with ``namespace``

    slope
        The slope :math:`m`.

    intercept
        The intercept :math:`c`.

    output
        Name of the output column or the namespace of the output columns.

    """

    def linear(
        x: Union[pint.Quantity, float],
        slope: Union[pint.Quantity, float],
        intercept: Union[pint.Quantity, float],
    ) -> Union[pint.Quantity, float]:
        y = slope * x + intercept
        return y

    outk = []
    outv = []
    if column is not None:
        if isinstance(column, list):
            column = np.asarray(column)
        outk.append(_inp.get("column", output))
        outv.append(linear(column, slope, intercept))

    elif namespace is not None:
        for key, vals in namespace.items():
            if isinstance(vals, list):
                vals = np.asarray(vals)
            outk.append(_inp.get("namespace", output) + f"->{key}")
            outv.append(linear(vals, slope, intercept))

    ret = {}
    for k, v in zip(outk, outv):
        ret[k] = v
    return ret


@load_data(
    ("namespace", None, dict),
    ("column", None),
)
def apply_inverse(
    namespace: dict[str, pint.Quantity] = None,
    column: pint.Quantity = None,
    slope: Union[pint.Quantity, float] = None,
    intercept: Union[pint.Quantity, float] = None,
    output: str = "output",
    _inp: dict = {},
) -> dict[str, pint.Quantity]:
    """
    Allows for applying inverse linear functions / corrections to columns and namespaces.

    Given the linear formula, :math:`y = m \\times x + c`, this function returns :math:`x`,
    calculated from the input, i.e. :math:`x = (y - c) / m`,  where :math:`m` is the
    provided ``slope`` and :math:`c` is the provided ``intercept``.

    The arguments ``slope`` and ``intercept`` can be provided without units, in which
    case the units of ``column`` or ``namespace`` are preserved. If units of ``slope``
    and ``intercept``  are provided, they have to be dimensionally consistent.

    The arguments ``slope`` and ``intercept`` can be provided with uncertainties, in
    which case the uncertainty of the output value is calculated from linear uncertainty
    propagation.

    Parameters
    ----------
    namespace
        The prefix of the namespace for which uncertainties are to be replaced or
        stripped. Cannot be supplied along with ``column``.

    column
        The name of the column for which uncertainties are to be replaced or stripped.
        Cannot be supplied along with ``namespace``

    slope
        The slope :math:`m`.

    intercept
        The intercept :math:`c`.

    output
        Name of the output column or the namespace of the output columns.

    """

    def inverse(
        y: Union[pint.Quantity, float],
        slope: Union[pint.Quantity, float],
        intercept: Union[pint.Quantity, float],
    ) -> Union[pint.Quantity, float]:
        x = (y - intercept) / slope
        return x

    outk = []
    outv = []
    if column is not None:
        if isinstance(column, list):
            column = np.asarray(column)
        outk.append(_inp.get("column", output))
        outv.append(inverse(column, slope, intercept))

    elif namespace is not None:
        for key, vals in namespace.items():
            outk.append(_inp.get("namespace", output) + f"->{key}")
            outv.append(inverse(vals, slope, intercept))

    ret = {}
    for k, v in zip(outk, outv):
        ret[k] = v
    return ret
