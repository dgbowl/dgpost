"""
Module of transformations relevant to electrochemistry applications.

.. codeauthor:: Peter Kraus <peter.kraus@empa.ch>
"""
import pint
from yadg.dgutils import ureg
import numpy as np
from .helpers import columns_to_smiles, load_data, name_to_chem, electrons_from_smiles


@load_data(
    ("Ewe", "V"),
    ("R", "Ω"),
    ("I", "A"),
    ("Eref", "V"),
    ("T", "K"),
    ("n", None),
    ("Q", None),
    ("pH", None),
)
def nernst(
    Ewe: pint.Quantity,
    R: pint.Quantity = ureg.Quantity(0.0, "Ω"),
    I: pint.Quantity = ureg.Quantity(0.0, "A"),
    Eref: pint.Quantity = ureg.Quantity(0.0, "V"),
    T: pint.Quantity = ureg.Quantity(298.15, "K"),
    n: int = None,
    Q: float = None,
    pH: float = None,
    output: str = "Eapp",
) -> pint.Quantity:
    """
    Correct measured voltage to calculate the applied voltage, using corrections
    for Ohmic drop, reference potential vs RHE, and ionic concentration using 
    the Nernst equation, either by providing :math:`Q` and :math:`n`, or by 
    providing the :math:`pH`.

    This function corrects the measured voltage :math:`E_\\text{we}` to applied
    voltage :math:`E` by implementing the following equation:

    .. math::

        E &= E_\\text{we} + E_\\text{ref} + RI + E_N \\\\
        E_N &= - \\frac{\\overline{R} T}{nF} ln(Q) = \\frac{\\overline{R} T}{F} ln(10) \\text{pH}

    where :math:`E_\\text{ref}` is the potential of the reference electrode vs RHE,
    :math:`RI` is the product of cell resistance and applied current, :math:`\\overline{R}`
    is the molar gas constant, :math:`T` is the temperature, :math:`n` is the number
    of electrones transferred, :math:`F` is the Faraday constant, :math:`Q` is the 
    reaction quotient, and :math:`\\text{pH}` is the pH of the electrolyte.
    
    Parameters
    ----------
    Ewe
        The measured working potential with respect to the reference electrode.
        By default in V.

    R
        The resistance of the cell. By default in Ω. 

    I
        The applied current. By default in A.

    Eref
        The potential of the reference electrode with respect to RHE. 
        By default in V.
    
    T
        Temperature of the working electrode, used in the Nernst equation.
        By default 298.15 K.
    
    n
        Number of electrons transferred in the process described by the Nernst
        equation. Must be specified along ``Q``, cannot be specified with ``pH``.

    Q
        The reaction quotient of the components of the process described by the
        Nernst equation. Must be specified along ``n``, cannot be specified with
        ``pH``.

    pH
        The pH of the solution. This assumes the modelled process is the reduction
        of :math:`\\text{H}^+ \\rightarrow \\text{H}``, i.e. :math:`n = 1` and
        :math:`\\text{ln}(Q) = -\\text{ln}(10)\\text{pH}`

    output
        Name of the output variable. Defaults to ``Eapp``.
    
    Returns
    -------
    dict(output, E) : dict[str, pint.Quantity]
        Returns the calculated applied current in V.

    """
    E = Ewe
    if Eref is not None:
        E += Eref
    if R is not None and I is not None:
        E += R * I
    if (pH is not None) or (n is not None and Q is not None):
        EN = ureg("molar_gas_constant") * T / ureg("faraday_constant")
        if pH is not None:
            EN = pH * EN * np.log(10)
        else:
            EN = -(EN / n) * np.log(Q)
        E += EN
    return {output: E}


@load_data(
    ("rate", "mol/s", dict),
    ("I", "A"),
)
def fe(
    rate: dict[str, pint.Quantity],
    I: pint.Quantity,
    charges: dict = None,
    output: str = None,
) -> dict[str, pint.Quantity]:
    etot = abs(I) / (ureg("elementary_charge") * ureg("avogadro_constant"))
    pretag = "fe" if output is None else output
    ret = {}
    for k, v in rate.items():
        kchem = name_to_chem(k)
        n = electrons_from_smiles(kchem.smiles, ions=charges)
        ek = v * n
        fek = ek / etot
        tag = f"{pretag}->{k}"
        ret[tag] = fek.to_base_units()
    return ret
