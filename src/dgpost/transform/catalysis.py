"""
.. codeauthor::
    Peter Kraus

Includes functions to calculate the reactant- and product-based
:func:`~dgpost.transform.catalysis.conversion`, atom-based
:func:`~dgpost.transform.catalysis.selectivity`,
:func:`~dgpost.transform.catalysis.catalytic_yield`, and
:func:`~dgpost.transform.catalysis.atom_balance`.

.. rubric:: Functions

.. autosummary::

    atom_balance
    catalytic_yield
    conversion
    selectivity

Names of compounds within the specified mixtures are parsed to SMILES, and the
cross-matching of the ``feestock``, internal ``standard``, and the components of
``xin`` and ``xout`` (or ``rin`` and ``rout``) is performed using these SMILES.

.. note::

    This module assumes that the provided inlet and outlet compositions, whether
    mole fractions or molar rates, contain all species. This implies that the
    atomic balance of the inlet and outlet is near unity. If multiple inlet/outlet
    streams are present in the experiment, they need to be appropriately combined
    into a single namespace, e.g. using functions in the :mod:`dgpost.transform.rates`
    before using the functions in this module.

"""

import pint
import logging
import numpy as np
from typing import Iterable

logger = logging.getLogger(__name__)

from dgpost.utils.helpers import (
    name_to_chem,
    columns_to_smiles,
    default_element,
    element_from_formula,
    load_data,
    separate_data,
)


@load_data(
    ("xin", None, dict),
    ("xout", None, dict),
    ("rin", "mol/s", dict),
    ("rout", "mol/s", dict),
)
def conversion(
    feedstock: str,
    xin: dict[str, pint.Quantity] = None,
    xout: dict[str, pint.Quantity] = None,
    rin: dict[str, pint.Quantity] = None,
    rout: dict[str, pint.Quantity] = None,
    element: str = None,
    type: str = "product",
    standard: str = "N2",
    product: bool = None,
    output: str = None,
) -> dict[str, pint.Quantity]:
    """
    Calculates the conversion of ``feedstock`` :math:`f` into other products
    :math:`p`. The feedstock must be a species present in the inlet. By default,
    a product-based carbon conversion (:math:`\\text{el} = \\text{C}`), using
    data from the outlet, is computed.

    The product-based conversion :math:`X_p` is calculated using the outlet mole
    fractions :math:`x_\\text{out}(s)` of species :math:`s`, or the outlet molar
    rates :math:`\\dot{n}_\\text{out}(s)`. It is calculated on an elemental basis
    by considering the number of atoms of a certain element, :math:`n_\\text{el}`,
    as:

    .. math::

        X_{p, \\text{el}} =
        \\frac{\\sum_{s} n_\\text{el}(s) x_\\text{out}(s) - n_\\text{el}(f) x_\\text{out}(f)}
        {\\sum_{s} n_\\text{el}(s) x_\\text{out}(s)} =
        \\frac{\\sum_{s} n_\\text{el}(s) \\dot{n}_\\text{out}(s) - n_\\text{el}(f) \\dot{n}_\\text{out}(f)}
        {\\sum_{s} n_\\text{el}(s) \\dot{n}_\\text{out}(s)}

    Which requires the feedstock :math:`f` to be quantified in the outlet composition.

    If the outlet composition of :math:`f` is not defined or not suitable, the user
    should request a "mixed" conversion :math:`X_m`, which is calculated using:

    .. math::

        X_{m, \\text{el}} =
        \\frac{\\sum_{p}^{p\\ne f} n_\\text{el}(p) x_\\text{out}(p) f_e}
        {n_\\text{el}(f) x_\\text{in}(f)} =
        \\frac{\\sum_{p}^{p\\ne f} n_\\text{el}(p) \\dot{n}_\\text{out}(s)}
        {n_\\text{el}(f) \\dot{n}_\\text{in}(f)}

    Here, the expansion factor :math:`f_e` is introduced, which is defined as the
    expansion ratio of the internal ``standard`` in the mixture:
    :math:`f_e = x_\\text{out}(\\text{i.s.}) / x_\\text{in}(\\text{i.s.})`. The
    internal standard is set to N2 by default. When molar rates :math:`\\dot{n}`
    are used, accounting for expansion in this way is not necessary.

    .. note::

        Calculating mixed conversion :math:`X_m` using inlet mole fraction
        of feedstock is not ideal and should be avoided, as the value is strongly
        convoluted with the :func:`atom_balance` of the mixtures.

    Finally, the calculation of reactant-based (or feedstock-based) conversion,
    :math:`X_r`, proceeds as follows:

    .. math::

        X_{r} = \\frac{x_\\text{in}(f) -  x_\\text{out}(f) f_e}{x_\\text{in}(f)} =
        \\frac{\\dot{n}_\\text{in}(f) - \\dot{n}_\\text{out}(f)}{\\dot{n}_\\text{in}(f)}

    The selection of the element :math:`\\text{el}` is meaningless for the reactant
    -based conversion.

    .. warning::

        Note that the calculated values of :math:`X_p`, :math:`X_m`, and :math:`X_r`
        will differ from one another in cases where the atomic balances of the inlet
        and outlet mixtures are different from unity!

    Parameters
    ----------
    feedstock
        Name of the feedstock. Parsed into SMILES and matched against ``xin`` and
        ``xout``.

    xin
        A dictionary containing the composition of the inlet mixture with the names
        of the chemicals as :class:`str` keys. Has to be supplied with ``xout``.
        Cannot be supplied with ``rin`` or ``rout``.

    xout
        A dictionary containing the composition of the outlet mixture with the names
        of the chemicals as :class:`str` keys. Has to be supplied with ``xin``.
        Cannot be supplied with ``rin`` or ``rout``.

    rin
        A dictionary containing the molar rates of species in the inlet mixture
        with the names of the chemicals as :class:`str` keys. Has to be supplied
        with ``rout``. Cannot be supplied with ``xin`` or ``xout``.

    rout
        A dictionary containing the molar rates of species in the outlet mixture
        with the names of the chemicals as :class:`str` keys. Has to be supplied
        with ``rin``. Cannot be supplied with ``xin`` or ``xout``.

    element
        Name of the element for determining conversion. If not specified, set to the
        highest-priority (C > H > O) element in ``feedstock``.

    type
        Conversion type. Can be one of ``{"reactant", "product", "mixed"}``, selecting
        the conversion calculation algorithm.

    product
        **Deprecated.** Switches between reactant and product-based conversion.

    standard
        Internal standard for normalizing the compositions. By default set to "N2".
        Only used when ``xin`` and ``xout`` are supplied.

    output
        A :class:`str` name of the output variable.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A :class:`dict` containing the calculated conversion with ``output`` as its key.

    """
    if product is not None:
        logger.warning(
            "Specifying reactant- and product-based conversion using "
            f"'product' is deprecated and will stop working in dgpost-2.0. "
            "Use 'type={product,reactant,mixed}' instead."
        )
        type = "product" if product else "reactant"
    assert (xin is None and xout is None) or (rin is None and rout is None)
    inp = xin if rin is None else rin
    out = xout if rout is None else rout
    smiles = columns_to_smiles(inp=inp, out=out)
    fchem = name_to_chem(feedstock)
    fsmi = fchem.smiles
    fform = fchem.formula
    assert fsmi in smiles, f"conversion: Feedstock '{feedstock}' not present."
    fd = smiles[fsmi]

    if element is None:
        element = default_element(fform)

    # expansion factor
    if xin is None and xout is None:
        logger.debug("Calculation using molar rates. Expansion factor set to 1.0.")
        exp = 1.0
    else:
        logger.debug(
            "Calculation using molar fractions. Expansion factor derived from '%s'",
            standard,
        )
        sd = smiles[name_to_chem(standard).smiles]
        exp = inp[sd["inp"]] / out[sd["out"]]

    # reactant-based conversion
    if type == "reactant":
        assert "inp" in fd, f"Feedstock '{feedstock}' not in inlet."
        assert "out" in fd, f"Feedstock '{feedstock}' not in outlet."
        logger.debug("Calculating reactant-based conversion.")
        dfsm = inp[fd["inp"]] - out[fd["out"]] * exp
        Xr = dfsm / inp[fd["inp"]]
        tag = f"{'Xr' if output is None else output}->{feedstock}"
        ret = {tag: Xr}

    # product-based conversion
    else:
        assert "inp" in fd, f"Feedstock '{feedstock}' not in inlet."
        f_in = inp[fd["inp"]] * element_from_formula(fform, element)
        nat_out = f_in * 0.0

        if "out" in fd:
            f_out = out[fd["out"]] * element_from_formula(fform, element)
        else:
            f_out = 0

        for v in smiles.values():
            if "out" in v:
                formula = v["chem"].formula
                dnat = out[v["out"]] * element_from_formula(formula, element)
                if isinstance(dnat, Iterable):
                    dnatn, _, _ = separate_data(dnat)
                    dnat.m[np.isnan(dnatn)] = 0
                nat_out += dnat
        if type == "product":
            logger.debug("Calculating product-based conversion using reactant outlet.")
            Xp = (nat_out - f_out) / nat_out
            prefix = f"Xp_{element}" if output is None else output
        elif type == "mixed":
            logger.debug("Calculating product-based conversion using reactant inlet.")
            Xp = (nat_out - f_out) / f_in
            prefix = f"Xm_{element}" if output is None else output
        tag = f"{prefix}->{feedstock}"
        ret = {tag: Xp}
    return ret


@load_data(
    ("xout", None, dict),
    ("rout", "mol/s", dict),
)
def selectivity(
    feedstock: str,
    xout: dict[str, pint.Quantity] = None,
    rout: dict[str, pint.Quantity] = None,
    element: str = None,
    output: str = None,
) -> dict[str, pint.Quantity]:
    """
    Calculates product-based atomic selectivities of all species :math:`s`,
    excluding the ``feedstock`` :math:`f`. The sum of selectivities is normalised
    to unity. Works with both mole fractions :math:`x` as well as molar production
    rates :math:`\\dot{n}`:

    .. math::

        S_\\text{el}(p) =
        \\frac{\\sum_{p}^{p \\ne f} n_\\text{el}(p) x_\\text{out}(p)}
        {\\sum_{s} n_\\text{el}(s) x_\\text{out}(s)} =
        \\frac{\\sum_{p}^{p \\ne f} n_\\text{el}(p) \\dot{n}_\\text{out}(p)}
        {\\sum_{s} n_\\text{el}(s) \\dot{n}_\\text{out}(s)}

    Only the outlet fractions/rates are considered. The sum on in the numerator runs
    over all products :math:`p` (i.e. :math:`p \\ne f`), while the sum in the
    denominator runs over all species :math:`s`. The value :math:`n_\\text{el}(s)`
    is the number of atoms of element :math:`\\text{el}` in species :math:`s`.

    .. note::

        The selectivity calculation assumes that all products have been determined;
        it provides no information about the mass or atomic balance.

    .. note::

        When molar rates :math:`\\dot{n}` are used, only creation rates (i.e.
        where :math:`\\dot{n}(p) > 0`) are used for calculation of selectivity.

    Parameters
    ----------
    feedstock
        Name of the feedstock. Parsed into SMILES and matched against the specified
        inlet and outlet species

    xout
        Prefix of the columns determining the outlet composition.

    rout
        Prefix of the columns determining the outlet molar rates.

    element
        The element for determining conversion. If not specified, set from ``feedstock``
        using :func:`dgpost.transform.chemhelpers.default_element`.

    output
        A :class:`str` prefix for the output variables.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A :class:`dict` containing the calculated selectivities using ``output`` as
        the prefix for each key.

    """
    assert xout is None or rout is None
    out = xout if rout is None else rout

    smiles = columns_to_smiles(out=out)
    fchem = name_to_chem(feedstock)
    fsmi = fchem.smiles
    fform = fchem.formula
    assert fsmi in smiles, f"selectivity: Feedstock '{feedstock}' not present."

    if element is None:
        element = default_element(fform)

    nat_out = None
    for k, v in smiles.items():
        if k != fsmi and "out" in v:
            formula = v["chem"].formula
            dnat = out[v["out"]] * element_from_formula(formula, element)
            if isinstance(dnat, Iterable):
                dnatn, _, _ = separate_data(dnat)
                dnat.m[np.isnan(dnatn)] = 0
            if nat_out is None:
                nat_out = dnat
            else:
                nat_out += dnat
    ret = {}
    for k, v in smiles.items():
        if k != fsmi and "out" in v:
            formula = v["chem"].formula
            els = element_from_formula(formula, element)
            if els > 0:
                nat = out[v["out"]] * els
                Sp = nat * (nat > 0) / nat_out
                pretag = f"Sp_{element}" if output is None else output
                tag = f"{pretag}->{v['out']}"
                ret[tag] = Sp
    return ret


@load_data(
    ("xin", None, dict),
    ("xout", None, dict),
    ("rin", "mol/s", dict),
    ("rout", "mol/s", dict),
)
def catalytic_yield(
    feedstock: str,
    xin: dict[str, pint.Quantity] = None,
    xout: dict[str, pint.Quantity] = None,
    rin: dict[str, pint.Quantity] = None,
    rout: dict[str, pint.Quantity] = None,
    element: str = None,
    standard: str = "N2",
    type: str = "product",
    output: str = None,
) -> None:
    """
    Calculates the catalytic yield :math:`Y_p`, defined as the product of conversion
    and selectivity. By default, uses product-based conversion of feedstock for an
    internal consistency with selectivity. The sum of all yields is equal to the
    conversion. Implicitly runs :func:`conversion` and :func:`selectivity` on the
    :class:`pd.DataFrame`:

    .. math::

        Y_{p, \\text{el}}(s) = X_{p, \\text{el}}(s) \\times S_{p, \\text{el}}(s)

    Where :math:`s` is the product species, and the subscript :math:`p` denotes it
    is a product-based quantity, with respect to element :math:`\\text{el}`.

    Parameters
    ----------
    xin
        Prefix of the columns determining the inlet composition.

    xout
        Prefix of the columns determining the outlet composition.

    feedstock
        Name of the feedstock. Parsed into SMILES and matched against ``xin`` and
        ``xout``.

    element
        The element for determining conversion. If not specified, set from ``feedstock``
        using :func:`dgpost.transform.chemhelpers.default_element`.

    standard
        Internal standard for normalizing the compositions. By default set to "N2".

    type
        Select conversion calculation algorithm, see
        :func:`~dgpost.transform.catalysis.conversion`.

    output
        A :class:`str` prefix for the output variables.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A :class:`dict` containing the calculated yields using ``output`` as
        the prefix for each key.

    """
    fchem = name_to_chem(feedstock)
    if element is None:
        element = default_element(fchem.formula)

    ret_Xp = conversion(
        feedstock=feedstock,
        xin=xin,
        xout=xout,
        rin=rin,
        rout=rout,
        element=element,
        type=type,
        standard=standard,
    )
    ret_Sp = selectivity(feedstock=feedstock, xout=xout, rout=rout, element=element)

    if f"Xp_{element}->{feedstock}" in ret_Xp:
        Xp = ret_Xp[f"Xp_{element}->{feedstock}"]
    else:
        logger.warning("Using Xm_%s to calculate Yp_%s.", element, element)
        Xp = ret_Xp[f"Xm_{element}->{feedstock}"]

    ret = {}
    for k, v in ret_Sp.items():
        Yp = v * Xp
        pretag = f"Yp_{element}" if output is None else output
        name = k.split("->")[1]
        tag = f"{pretag}->{name}"
        ret[tag] = Yp
    return ret


@load_data(
    ("xin", None, dict),
    ("xout", None, dict),
    ("rin", "mol/s", dict),
    ("rout", "mol/s", dict),
)
def atom_balance(
    xin: dict[str, pint.Quantity] = None,
    xout: dict[str, pint.Quantity] = None,
    rin: dict[str, pint.Quantity] = None,
    rout: dict[str, pint.Quantity] = None,
    element: str = "C",
    standard: str = "N2",
    output: str = None,
) -> None:
    """
    Calculates the atom balance of an ``element`` :math:`\\text{el}` between the
    inlet and outlet mixtures. The total number of atoms of the specified element
    is compared between between the inlet and outlet, normalized by an internal
    ``standard`` if necessary:

    .. math::

        \\text{atbal}_\\text{el} =
        \\frac{\\sum_s n_\\text{el}(s) x_\\text{out}(s) f_e}
        {\\sum_s n_\\text{el}(s) x_\\text{in}(s)} =
        \\frac{\\sum_s n_\\text{el}(s) \\dot{n}_\\text{out}(s)}
        {\\sum_s n_\\text{el}(s) \\dot{n}_\\text{in}(s)}

    Here the sum runs over all species :math:`s`, :math:`n_\\text{el}(s)` is the
    number of atoms of element :math:`\\text{el}` in :math:`s`,  and :math:`f_e`
    is the expansion factor calculated using the internal ``standard`` as
    :math:`f_e = x_\\text{out}(\\text{i.s.}) / x_\\text{in}(\\text{i.s.})`.

    Parameters
    ----------
    xin
        Prefix of the columns determining the inlet composition as a mole fraction.

    xout
        Prefix of the columns determining the outlet composition as a mole fraction.

    rin
        Prefix of the columns determining the inlet composition as a molar rate.

    rout
        Prefix of the columns determining the outlet composition as a molar rate.

    element
        The element for determining conversion. If not specified, set to ``"C"``.

    standard
        Internal standard for normalizing flows. By default set to ``"N2"``.

    output
        A :class:`str` prefix for the output variables.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A :class:`dict` containing the calculated atomic balance using ``output`` as
        the key.

    """
    assert (xin is None and xout is None) or (rin is None and rout is None)
    inp = xin if rin is None else rin
    out = xout if rout is None else rout
    smiles = columns_to_smiles(inp=inp, out=out)

    if rin is None:
        sd = smiles[name_to_chem(standard).smiles]
        exp = inp[sd["inp"]] / out[sd["out"]]
    else:
        exp = 1.0

    nat_in = None
    nat_out = None
    for k, v in smiles.items():
        formula = v["chem"].formula
        if "inp" in v:
            din = inp[v["inp"]] * element_from_formula(formula, element)
            nat_in = din if nat_in is None else nat_in + din
        if "out" in v:
            dout = exp * out[v["out"]] * element_from_formula(formula, element)
            nat_out = dout if nat_out is None else nat_out + dout
    dnat = nat_in - nat_out
    atbal = 1 - dnat / nat_in
    tag = f"atbal_{element}" if output is None else output

    return {tag: atbal}
