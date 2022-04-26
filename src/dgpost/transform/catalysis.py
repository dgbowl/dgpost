"""
**catalysis**: common calculations in catalytic testing
-------------------------------------------------------
.. codeauthor:: 
    Peter Kraus

Includes functions to calculate the reactant- and product-based 
:func:`~dgpost.transform.catalysis.conversion`, atom-based 
:func:`~dgpost.transform.catalysis.selectivity`, catalytic 
:func:`~dgpost.transform.catalysis.yield`, and 
:func:`~dgpost.transform.catalysis.atom_balance`.

Names of compounds within the specified mixtures are parsed to SMILES, and the
cross-matching of the ``feestock``, internal ``standard``, and the components of 
``xin`` and ``xout`` is performed using these SMILES.

.. note::
    This module assumes that the provided inlet (``xin``) and outlet (``xout``) 
    compositions contains all species, and that the atomic balance of the inlet and 
    outlet is near unity. If multiple inlet/outlet streams are present in the 
    experiment, they need to be appropriately combined into a single namespace, e.g.
    using functions in the :mod:`dgpost.transform.rates` before using the functions 
    in this module.

"""

import pint


from .helpers import (
    name_to_chem,
    columns_to_smiles,
    default_element,
    element_from_formula,
    load_data,
)


@load_data(
    ("xin", None, dict),
    ("xout", None, dict),
)
def conversion(
    xin: dict[str, pint.Quantity],
    xout: dict[str, pint.Quantity],
    feedstock: str,
    element: str = None,
    product: bool = True,
    standard: str = "N2",
    output: str = None,
) -> dict[str, pint.Quantity]:
    """
    Calculates the conversion of ``feedstock``, a species present in ``xin``. By
    default, a product-based carbon conversion (using data from ``xout``) is computed.

    Parameters
    ----------
    feedstock
        Name of the feedstock. Parsed into SMILES and matched against ``xin`` and
        ``xout``.

    xin
        A dictionary containing the composition of the inlet mixture with the names
        of the chemicals as :class:`str` keys.

    xout
        A dictionary containing the composition of the outlet mixture with the names
        of the chemicals as :class:`str` keys.

    element
        Name of the element for determining conversion. If not specified, set to the
        highest-priority (C > H > O) element in ``feedstock``.

    product
        Product-based conversion toggle. Default is ``True``.

    standard
        Internal standard for normalizing the compositions. By default set to "N2".

    output
        A :class:`str` name of the output variable.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A :class:`dict` containing the calculated conversion with ``output`` as its key.

    """

    smiles = columns_to_smiles(xin=xin, xout=xout)
    fchem = name_to_chem(feedstock)
    fsmi = fchem.smiles
    fform = fchem.formula
    fd = smiles[fsmi]
    assert fsmi in smiles, f"conversion: Feedstock '{feedstock}' not present."
    assert "xin" in smiles[fsmi], f"conversion: Feedstock '{feedstock}' not in inlet."

    if element is None:
        element = default_element(fform)

    # expansion factor
    sd = smiles[name_to_chem(standard).smiles]
    exp = xin[sd["xin"]] / xout[sd["xout"]]

    # reactant-based conversion
    if not product:
        dfsm = xin[fd["xin"]] - xout[fd["xout"]] * exp
        Xr = dfsm / xin[fd["xin"]]
        tag = f"{'Xr' if output is None else output}->{feedstock}"
        ret = {tag: Xr}

    # product-based conversion
    else:
        f_out = xout[fd["xout"]] * element_from_formula(fform, element)
        nat_out = f_out * 0.0
        for v in smiles.values():
            if "xout" in v:
                formula = v["chem"].formula
                dnat = xout[v["xout"]] * element_from_formula(formula, element)
                nat_out += dnat
        Xp = (nat_out - f_out) / nat_out
        prefix = f"Xp_{element}" if output is None else output
        tag = f"{prefix}->{feedstock}"
        ret = {tag: Xp}
    return ret


@load_data(
    ("xin", None, dict),
    ("xout", None, dict),
)
def selectivity(
    xin: dict[str, pint.Quantity],
    xout: dict[str, pint.Quantity],
    feedstock: str,
    element: str = None,
    output: str = None,
) -> dict[str, pint.Quantity]:
    """
    Calculates product-based atomic selectivities, excluding the feedstock. The sum
    of selectivities is normalised to unity.

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

    output
        A :class:`str` prefix for the output variables.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A :class:`dict` containing the calculated selectivities using ``output`` as
        the prefix for each key.

    """
    smiles = columns_to_smiles(xin=xin, xout=xout)
    fchem = name_to_chem(feedstock)
    fsmi = fchem.smiles
    fform = fchem.formula
    assert fsmi in smiles, f"selectivity: Feedstock '{feedstock}' not present."

    if element is None:
        element = default_element(fform)

    nat_out = None
    for k, v in smiles.items():
        if k != fsmi and "xout" in v:
            formula = v["chem"].formula
            dnat = xout[v["xout"]] * element_from_formula(formula, element)
            if nat_out is None:
                nat_out = dnat
            else:
                nat_out += dnat
    ret = {}
    for k, v in smiles.items():
        if k != fsmi and "xout" in v:
            formula = v["chem"].formula
            els = element_from_formula(formula, element)
            if els > 0:
                Sp = xout[v["xout"]] * els / nat_out
                pretag = f"Sp_{element}" if output is None else output
                tag = f"{pretag}->{v['xout']}"
                ret[tag] = Sp
    return ret


@load_data(
    ("xin", None, dict),
    ("xout", None, dict),
)
def catalytic_yield(
    xin: dict[str, pint.Quantity],
    xout: dict[str, pint.Quantity],
    feedstock: str,
    element: str = None,
    standard: str = "N2",
    output: str = None,
) -> None:
    """
    Calculates the catalytic yield, defined as the product of conversion and
    selectivity. Uses product-based conversion of feedstock for consistency with
    selectivity. The sum of all yields is equal to the conversion. Implicitly runs
    :func:`conversion` and :func:`selectivity` on the dataframe.

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
        element=element,
        product=True,
        standard=standard,
    )
    ret_Sp = selectivity(feedstock=feedstock, xin=xin, xout=xout, element=element)

    Xp = ret_Xp[f"Xp_{element}->{feedstock}"]

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
    ("fin", None),
    ("fout", None),
)
def atom_balance(
    xin: dict[str, pint.Quantity],
    xout: dict[str, pint.Quantity],
    fin: pint.Quantity = None,
    fout: pint.Quantity = None,
    element: str = "C",
    standard: str = "N2",
    output: str = None,
) -> None:
    """
    Calculates atom balance. The total number of atoms of the specified element is
    compared between between the inlet and outlet, normalized by an internal standard,
    or optionally weighed by the supplied flows.

    Parameters
    ----------
    xin
        Prefix of the columns determining the inlet composition.

    xout
        Prefix of the columns determining the outlet composition.

    fin
        Inlet flow. If not supplied, assumed to be equal to outlet flow.

    fout
        Outlet flow. If not supplied, assumed to be equal to inlet flow.

    element
        The element for determining conversion. If not specified, set to ``"C"``.

    standard
        Internal standard for normalizing flows. By default set to ``"N2"``.
        Overriden when ``fin`` and ``fout`` are set.

    output
        A :class:`str` prefix for the output variables.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A :class:`dict` containing the calculated atomic balance using ``output`` as
        the key.

    """
    smiles = columns_to_smiles(xin=xin, xout=xout)

    assert standard is not None or (
        fin is not None and fout is not None
    ), f"atom_balance: Neither 'standard' nor 'fin' and 'fout' are defined. "

    if fin is None or fout is None:
        sd = smiles[name_to_chem(standard).smiles]
        exp = xin[sd["xin"]] / xout[sd["xout"]]
    else:
        exp = fin / fout

    nat_in = None
    nat_out = None
    for k, v in smiles.items():
        formula = v["chem"].formula
        if "xin" in v:
            din = xin[v["xin"]] * element_from_formula(formula, element)
            nat_in = din if nat_in is None else nat_in + din
        if "xout" in v:
            dout = exp * xout[v["xout"]] * element_from_formula(formula, element)
            nat_out = dout if nat_out is None else nat_out + dout
    dnat = nat_in - nat_out
    atbal = 1 - dnat / nat_in
    tag = f"atbal_{element}" if output is None else output

    return {tag: atbal}
