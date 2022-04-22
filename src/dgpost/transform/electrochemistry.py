"""
``electrochemistry``: calculations relevant in electrochemistry
---------------------------------------------------------------
.. codeauthor:: 
    Peter Kraus

Module of transformations relevant to electrochemistry applications. Includes
applied voltage correction via the Nernst equation, Faradaic efficiency calculation,
as well as the calculation of total charge from current and timestamps, and the 
average current from the total charge and timestamps.

"""
import pint
from yadg.dgutils import ureg
import numpy as np
import pandas as pd
from .helpers import load_data, name_to_chem, electrons_from_smiles


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
        EN = ureg("molar_gas_constant") * T.to("K") / ureg("faraday_constant")
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
    charges: dict[str, int],
    output: str = None,
) -> dict[str, pint.Quantity]:
    """
    Calculate the Faradaic efficiency :math:`\\eta_F` from a set of molar rates
    :math:`\\dot{n}`` corresponding to a single mixture, and the applied current
    :math:`I` required to produce that mixture from a source mixture. A set of
    formal atomic charges corresponding to those in the species comprising the
    source mixture has to be supplied.

    This function implements the following equation to calculate :math:`\\eta_F`:

    .. math::

        \\eta_F(x) = \\frac{n_\\text{el}(x)\\dot{n}(x)}{I}

    where :math:`x` is a species in the mixture, :math:`n_\\text{el}(x)` is the number
    of electrons required to produce :math:`x` from the ions specified in the source
    mixture, and :math:`\\dot{n}(x)` is the molar rate (production or flow) of species
    :math:`x`.

    Parameters
    ----------
    rate
        A :class:`dict` of molar flow or production rates of species in a mixture.
        By default in mol/l.

    I
        The applied current. By default in A.

    charges
        A :class:`dict` of formal atomic/ionic charges of atoms in the source
        mixture.

    output
        Name of the prefix for the species in the output variable. Defaults to ``fe``.

    Returns
    -------
    dict(output, E) : dict[str, pint.Quantity]
        Returns the calculated Faradaic efficiencies.

    """
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


@load_data(
    ("time", "s", pd.Index),
    ("I", "A"),
)
def charge(
    time: pint.Quantity,
    I: pint.Quantity,
    t0: pint.Quantity = None,
    output: str = "Q",
) -> dict[str, pint.Quantity]:
    """
    Calculate charge as a time-integral of the electric current.

    Parameters
    ----------
    time
        An array of timestamps at which the instantaneous current was measured.

    I
        Values of the instantaneous current.

    t0
        An optional timestamp representing the time at which charge was zero. If not 
        supplied, the first value in the ``time`` array will be used, with the charge 
        at that timestamp set to zero.

    output
        Prefix of the columns where the calculated rate will be stored.


    Returns
    -------
    dict(output, Q) : dict[str, pint.Quantity]
        Returns the integrated electrical charge.

    """
    nts = len(time)
    if nts == 1 and t0 is not None:
        raise RuntimeError("A single timestep was provided without specifying 't0'.")
    elif t0 is not None:
        dt = np.diff(np.insert(time, 0, t0))
    else:
        dt = np.insert(np.diff(time), 0, ureg.Quantity(0, "s"))
    dq = I * dt
    Q = np.cumsum(dq).to_base_units()
    ret = {output: Q}
    return ret