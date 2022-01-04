"""
Module of transformations relevant to catalysis applications.

For all user-facing function in this module, the data is extracted from the 
:class:`pd.DataFrame` supplied as ``df``. The inlet and outlet compositions are
specified using ``xin`` and ``xout``, and they are taken to be all columns in ``df`` 
matching the format ``{xin|xout}->*``. The ``*`` denotes species names, which are 
parsed to SMILES. Matching of ``feestock``, ``standard``, and components of ``xin``
and ``xout`` is performed using these SMILES.

.. note::
    This module assumes that the provided inlet (``xin``) and outlet (``xout``) 
    compositions contains all species, and that the atomic balance of the inlet and 
    outlet is near unity. If multiple inlet/outlet streams are present in the 
    experiment, they need to be appropriately combined into a single ``xin``/``xout`` 
    using functions in the :mod:`dgpost.transform.mixture` before using the functions 
    in this module.

"""
import pandas as pd
import uncertainties as uc
import numpy as np

from dgpost.transform.chemhelpers import (
    columns_to_smiles,
    default_element,
    element_from_formula,
)
from chemicals.identifiers import search_chemical


def conversion(
    df: pd.DataFrame,
    feedstock: str,
    xin: str = "xin",
    xout: str = "xout",
    element: str = None,
    product: bool = True,
    standard: str = "N2",
) -> None:
    """
    Calculates the conversion of ``feedstock``, a species present in ``xin``. By
    default, a product-based carbon conversion (using data from ``xout``) is computed.

    Parameters
    ----------
    df
        A pandas dataframe.

    feedstock
        Name of the feedstock. Parsed into SMILES and matched against ``xin`` and
        ``xout``.

    xin
        Prefix of the columns determining the inlet composition.

    xout
        Prefix of the columns determining the outlet composition.

    element
        Name of the element for determining conversion. If not specified, set to the
        highest-priority element in ``feedstock``: "C" > "O" > "H" > ...

    product
        Product-based conversion toggle. Default is ``True``.

    standard
        Internal standard for normalizing flows. By default set to "N2".

    """
    smiles = columns_to_smiles(df, [xin, xout])

    f = search_chemical(feedstock)
    fsm = f.smiles
    assert fsm in smiles, f"conversion: Feedstock '{feedstock}' not present."
    assert xin in smiles[fsm], f"conversion: Feedstock '{feedstock}' not in inlet."

    if element is None:
        element = default_element(f.formula)

    s = search_chemical(standard)
    exp = df[smiles[s.smiles]["xin"]] / df[smiles[s.smiles]["xout"]]

    # reactant-based conversion
    if not product:
        dfsm = df[smiles[fsm]["xin"]] - df[smiles[fsm]["xout"]] * exp
        Xr = dfsm / df[smiles[fsm]["xin"]]
        tag = f"Xr->{feedstock}"
        df[tag] = Xr
    # product-based conversion
    else:
        formula = f.formula
        f_out = df[smiles[fsm]["xout"]] * element_from_formula(formula, element)
        nat_out = np.zeros(f_out.shape[0])
        if isinstance(f_out.iloc[0], uc.UFloat):
            nat_out = nat_out * uc.ufloat(0, 0)
        for k, v in smiles.items():
            if "xout" in v:
                formula = v["chem"].formula
                dnat = df[v["xout"]] * element_from_formula(formula, element)
                nat_out += dnat
        Xp = (nat_out - f_out) / nat_out
        tag = f"Xp_{element}->{feedstock}"
        df[tag] = Xp
    return None


def selectivity(
    df: pd.DataFrame,
    feedstock: str,
    xin: str = "xin",
    xout: str = "xout",
    element: str = None,
) -> None:
    """
    Calculates product-based elemental selectivities, excluding the feedstock. The sum
    of selectivities is normalised to unity.

    Parameters
    ----------
    df
        A pandas dataframe.

    feedstock
        Name of the feedstock. Parsed into SMILES and matched against ``xin`` and
        ``xout``.

    xin
        Prefix of the columns determining the inlet composition.

    xout
        Prefix of the columns determining the outlet composition.

    element
        The element for determining conversion. If not specified, set from ``feedstock``
        using :func:`dgpost.transform.chemhelpers.default_element`.

    """
    smiles = columns_to_smiles(df, [xin, xout])

    f = search_chemical(feedstock)
    fsm = f.smiles
    assert fsm in smiles, f"selectivity: Feedstock '{feedstock}' not present."

    if element is None:
        element = default_element(f.formula)

    nat_out = np.zeros(df.shape[0])
    if isinstance(df[smiles[fsm]["xin"]].iloc[0], uc.UFloat):
        nat_out = nat_out * uc.ufloat(0, 0)
    for k, v in smiles.items():
        if k != fsm and "xout" in v:
            formula = v["chem"].formula
            dnat = df[v["xout"]] * element_from_formula(formula, element)
            nat_out += dnat

    for k, v in smiles.items():
        if k != fsm and "xout" in v:
            formula = v["chem"].formula
            els = element_from_formula(formula, element)
            if els > 0:
                Sp = df[v["xout"]] * els / nat_out
                name = v["xout"].split(xout)[1]
                tag = f"Sp_{element}{name}"
                df[tag] = Sp
    return None


def catalytic_yield(
    df: pd.DataFrame,
    feedstock: str,
    xin: str = "xin",
    xout: str = "xout",
    element: str = None,
    standard: str = "N2",
) -> None:
    """
    Calculates the catalytic yield, defined as the product of conversion and
    selectivity. Uses product-based conversion of feedstock for consistency with
    selectivity. The sum of all yields is equal to the conversion. Implicitly runs
    :func:`conversion` and :func:`selectivity` on the dataframe.

    Parameters
    ----------
    df
        A pandas dataframe.

    feedstock
        Name of the feedstock. Parsed into SMILES and matched against ``xin`` and
        ``xout``.

    xin
        Prefix of the columns determining the inlet composition.

    xout
        Prefix of the columns determining the outlet composition.

    element
        The element for determining conversion. If not specified, set from ``feedstock``
        using :func:`dgpost.transform.chemhelpers.default_element`.

    standard
        Internal standard for normalizing flows. By default set to ``"N2"``.

    """
    f = search_chemical(feedstock)
    if element is None:
        element = default_element(f.formula)

    conversion(df, feedstock, xin, xout, element, True, standard)
    selectivity(df, feedstock, xin, xout, element)

    Xp = df[f"Xp_{element}->{feedstock}"]
    smiles = columns_to_smiles(df, f"Sp_{element}")

    for k, v in smiles.items():
        Sp = df[v[f"Sp_{element}"]]
        Yp = Sp * Xp
        name = v[f"Sp_{element}"].split("->")[1]
        tag = f"Yp_{element}->{name}"
        df[tag] = Yp

    return None


def atom_balance(
    df: pd.DataFrame,
    xin: str = "xin",
    xout: str = "xout",
    element: str = "C",
    standard: str = "N2",
    fin: str = None,
    fout: str = None,
) -> None:
    """
    Calculates atom balance. The total number of atoms of the specified element is
    compared between between the inlet and outlet, normalized by an internal standard,
    or optionally weighed by the supplied flows.

    Parameters
    ----------
    df
        A pandas dataframe.

    xin
        Prefix of the columns determining the inlet composition.

    xout
        Prefix of the columns determining the outlet composition.

    element
        The element for determining conversion. If not specified, set to ``"C"``.

    standard
        Internal standard for normalizing flows. By default set to ``"N2"``.
        Overriden when ``fin`` and ``fout`` are set.

    fin
        Inlet flow. If not supplied, assumed to be equal to outlet flow.

    fout
        Outlet flow. If not supplied, assumed to be equal to inlet flow.

    """
    smiles = columns_to_smiles(df, [xin, xout])

    assert (
        standard is not None or fin is not None and fout is not None
    ), f"atom_balance: Neither 'standard' nor 'fin' and 'fout' are defined. "

    if fin is None or fout is None:
        s = search_chemical(standard)
        exp = df[smiles[s.smiles]["xin"]] / df[smiles[s.smiles]["xout"]]
    else:
        exp = df[fin] / df[fout]

    nat_in = np.zeros(exp.shape[0])
    nat_out = np.zeros(exp.shape[0])
    if isinstance(exp.iloc[0], uc.UFloat):
        nat_in = nat_in * uc.ufloat(0, 0)
        nat_out = nat_out * uc.ufloat(0, 0)

    for k, v in smiles.items():
        formula = v["chem"].formula
        if "xin" in v:
            nat_in += df[v["xin"]] * element_from_formula(formula, element)
        if "xout" in v:
            nat_out += exp * df[v["xout"]] * element_from_formula(formula, element)
    dnat = nat_in - nat_out
    abal = 1 - dnat / nat_in

    df[f"atbal_{element}"] = abal

    return None
