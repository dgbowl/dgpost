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
import numpy as np
from dgpost.utils.helpers import (
    load_data,
    separate_data,
    columns_to_smiles,
    kwarg_to_quantity,
    fill_nans,
)
from collections import defaultdict
from typing import Union
from uncertainties import unumpy as unp

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
    Combines two namespaces into one, either summing or merging entries.

    Unit checks are performed, with the resulting units corresponding to the units in
    namespace ``a``. By default, the output namespace is set to ``a``. Optionally, the
    keys in each namespace can be treated as chemicals instead of strings (i.e. "C2H6"
    and "ethane" would be summed / merged).

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
                aa = fill_nans(aa)
                bb = fill_nans(bb)
            if conflicts == "sum":
                ret[v["a"]] = aa + bb
            elif conflicts == "replace":
                ret[v["a"]] = bb.to(u)
            else:
                raise ValueError(f"Unknown value of 'conflicts': {conflicts}")
        elif "a" in v:
            aa = a[v["a"]]
            if fillnan:
                aa = fill_nans(aa)
            ret[v["a"]] = aa
        elif "b" in v:
            bb = b[v["b"]].to(u)
            if fillnan:
                bb = fill_nans(bb)
            ret[v["b"]] = bb

    if output is None:
        output = _inp.get("a", "c")

    out = {}
    for k, v in ret.items():
        out[f"{output}->{k}"] = v
    return out


@load_data(
    ("namespace", None, dict),
)
def sum_namespace(
    namespace: dict[str, pint.Quantity],
    output: str = "output",
    fillnan: bool = True,
    _inp: dict = {},
) -> dict[str, pint.Quantity]:
    """
    Sums all entries within the provided namespace into one column, defined by ``output``.

    Parameters
    ----------
    namespace
        Namespace to be summed.

    fillnan
        Toggle whether ``NaN`` values within the columns ought to be treated as zeroes
        (when ``True``) or as ``NaN``. Default is ``True``.

    output
        Namespace of the returned dictionary. Defaults to ``output``.

    """
    ret = None

    for v in namespace.values():
        if fillnan:
            v = fill_nans(v, fillmag=0.0)
        if ret is None:
            ret = v
        else:
            ret += v
    return {output: ret}


@load_data(
    ("a", None),
    ("b", None),
)
def combine_columns(
    a: pint.Quantity,
    b: pint.Quantity,
    conflicts: str = "sum",
    fillnan: bool = True,
    output: str = None,
    _inp: dict = {},
) -> dict[str, pint.Quantity]:
    """
    Combines two columns into one, by summing or replacing missing elements.

    Unit checks are performed, with the resulting units corresponding to the units in
    column ``a``. By default, the output column is set to ``a``.

    Parameters
    ----------
    a
        Column ``a``.

    b
        Column ``b``.

    conflicts
        Conflict resolution scheme. Can be either ``"sum"`` where the two columns are
        summed, or ``"replace"``, where values in column ``a`` are overwritten by
        non-``np.nan`` values in column ``b``.

    fillnan
        Toggle whether ``NaN`` values within the columns ought to be treated as
        zeroes or as ``NaN``. Default is ``True``. Note that ``conflicts="replace"`` and
        ``fillnan="true"`` will lead to all ``NaN``s in column ``a`` to be set to zero.

    output
        Namespace of the returned dictionary. By defaults to the name of column ``a``.

    """

    if fillnan:
        a = fill_nans(a)
        b = fill_nans(b)
    if conflicts == "sum":
        ret = a + b
    elif conflicts == "replace":
        ret = np.where(np.isnan(b), a, b)
    else:
        raise ValueError(f"Unknown value of 'conflicts': {conflicts}")

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
@kwarg_to_quantity("slope", "intercept", "minimum", "maximum")
def apply_linear(
    namespace: dict[str, pint.Quantity] = None,
    column: pint.Quantity = None,
    slope: Union[pint.Quantity, float] = None,
    intercept: Union[pint.Quantity, float] = None,
    nonzero_only: bool = True,
    minimum: Union[pint.Quantity, float] = None,
    maximum: Union[pint.Quantity, float] = None,
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

    nonzero_only
        Whether the linear function should be applied to nonzero values of :math:`x` only,
        defaults to ``True``.

    minimum
        The minimum of the returned value. If the calculate value is below the minimum,
        the minimum is returned.

    maximum
        The maximum of the returned value. If the calculate value is above the maximum,
        the maximum is returned.

    output
        Name of the output column or the namespace of the output columns.

    """

    def linear(
        x: Union[pint.Quantity, float],
        slope: Union[pint.Quantity, float],
        intercept: Union[pint.Quantity, float],
        nonzero_only: bool = True,
        minimum: Union[pint.Quantity, float] = None,
        maximum: Union[pint.Quantity, float] = None,
    ) -> Union[pint.Quantity, float]:
        if isinstance(x, pint.Quantity) and isinstance(intercept, float):
            intercept = pint.Quantity(intercept, (slope * x).units)
        if nonzero_only:
            x = np.where(x > 0.0, x, np.nan)

        y = slope * x + intercept
        if maximum is not None:
            y = np.where(y > maximum, maximum, y)
        if minimum is not None:
            y = np.where(y < minimum, minimum, y)
        return y

    outk = []
    outv = []
    if column is not None:
        if isinstance(column, list):
            column = np.asarray(column)
        if output is not None:
            outk.append(output)
        else:
            outk.append(_inp.get("column", "output"))
        outv.append(linear(column, slope, intercept, nonzero_only, minimum, maximum))

    elif namespace is not None:
        for key, col in namespace.items():
            if isinstance(column, list):
                col = np.asarray(col)
            if output is not None:
                outk.append(f"{output}->{key}")
            else:
                outk.append(_inp.get("namespace", "output") + f"->{key}")
            outv.append(linear(col, slope, intercept, nonzero_only, minimum, maximum))

    ret = {}
    for k, v in zip(outk, outv):
        ret[k] = v
    return ret


@load_data(
    ("namespace", None, dict),
    ("column", None),
)
@kwarg_to_quantity("slope", "intercept", "minimum", "maximum")
def apply_inverse(
    namespace: dict[str, pint.Quantity] = None,
    column: pint.Quantity = None,
    slope: Union[pint.Quantity, float] = None,
    intercept: Union[pint.Quantity, float] = None,
    nonzero_only: bool = True,
    minimum: Union[pint.Quantity, float] = None,
    maximum: Union[pint.Quantity, float] = None,
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

    nonzero_only
        Whether the linear function should be applied to nonzero values of :math:`x` only,
        defaults to ``True``.

    minimum
        The minimum of the returned value. If the calculate value is below the minimum,
        the minimum is returned.

    maximum
        The maximum of the returned value. If the calculate value is above the maximum,
        the maximum is returned.

    output
        Name of the output column or the namespace of the output columns.

    """

    def inverse(
        y: Union[pint.Quantity, float],
        slope: Union[pint.Quantity, float],
        intercept: Union[pint.Quantity, float],
        nonzero_only: bool = True,
        minimum: Union[pint.Quantity, float] = None,
        maximum: Union[pint.Quantity, float] = None,
    ) -> Union[pint.Quantity, float]:
        if isinstance(y, pint.Quantity) and isinstance(intercept, float):
            intercept = pint.Quantity(intercept, y.units)
        if nonzero_only:
            y = np.where(y > 0.0, y, np.nan)

        x = (y - intercept) / slope
        if maximum is not None:
            x = np.where(x > maximum, np.nan, x)
        if minimum is not None:
            x = np.where(x < minimum, np.nan, x)
        return x

    outk = []
    outv = []
    if column is not None:
        if isinstance(column, list):
            column = np.asarray(column)
        if output is not None:
            outk.append(output)
        else:
            outk.append(_inp.get("column", "output"))
        outv.append(inverse(column, slope, intercept, nonzero_only, minimum, maximum))

    elif namespace is not None:
        for key, col in namespace.items():
            if isinstance(column, list):
                col = np.asarray(col)
            if output is not None:
                outk.append(f"{output}->{key}")
            else:
                outk.append(_inp.get("namespace", "output") + f"->{key}")
            outv.append(inverse(col, slope, intercept, nonzero_only, minimum, maximum))
    ret = {}
    for k, v in zip(outk, outv):
        ret[k] = v
    return ret
