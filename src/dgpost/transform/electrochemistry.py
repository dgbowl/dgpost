"""
.. codeauthor::
    Peter Kraus

Includes functions for calculating applied voltage correction via the
:func:`~dgpost.transform.electrochemistry.nernst` equation, calculation of the
Faradaic efficiency (:func:`~dgpost.transform.electrochemistry.fe`), as well as
the calculation of total :func:`~dgpost.transform.electrochemistry.charge`, and
the :func:`~dgpost.transform.electrochemistry.average_current` from the total
charge and timestamps.

.. rubric:: Functions

.. autosummary::

    average_current
    charge
    fe
    nernst

"""
import pint
import numpy as np
import pandas as pd
from typing import Iterable
from uncertainties import UFloat
from uncertainties import unumpy as unp
from dgpost.utils.helpers import (
    load_data,
    separate_data,
    name_to_chem,
    electrons_from_smiles,
)

ureg = pint.get_application_registry()


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
    R: pint.Quantity = pint.Quantity(0.0, "Ω"),
    I: pint.Quantity = pint.Quantity(0.0, "A"),
    Eref: pint.Quantity = pint.Quantity(0.0, "V"),
    T: pint.Quantity = pint.Quantity(298.15, "K"),
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
    voltage :math:`E`. For :math:`E_\\text{we} > 0~\\text{V}`, the following equation
    is used:

    .. math::

        E &= E_\\text{we} - R |I| + E_\\text{ref} + E_N \\\\
        E_N &= - \\frac{\\overline{R} T}{nF} ln(Q) = \\frac{\\overline{R} T}{F} ln(10) \\text{pH}

    where :math:`R |I|` is the product of cell resistance and the magnitude of the
    applied current, :math:`E_\\text{ref}` is the potential of the reference electrode
    vs RHE, :math:`\\overline{R}` is the molar gas constant, :math:`T` is the
    temperature, :math:`n` is the number of electrones transferred, :math:`F` is
    the Faraday constant, :math:`Q` is the reaction quotient, and :math:`\\text{pH}`
    is the pH of the electrolyte.

    .. note ::

        The Ohmic loss :math:`R |I|` always acts against the magnitude of the working
        potential :math:`E_\\text{we}`. If :math:`E_\\text{we} < 0~\\text{V}`, the Ohmic
        term :math:`R |I|` is added to :math:`E_\\text{we}` to reduce its magnitude.

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
        E -= np.sign(Ewe) * R * abs(I)
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
    if isinstance(etot.m, Iterable):
        etotn, _, _ = separate_data(etot)
        etot.m[etotn == 0] = np.NaN
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
    Calculate the total charge :math:`Q` as a time-integral of the electric current:

    .. math::

        Q_n = \\int_{t_0}^{t_n} I(t) dt = \\sum_0^n I_n (t_n - t_{n-1})

    where :math:`I_n` is the instantaneous current and :math:`t_n` is the time at the
    :math:`n`-th datapoint.

    Parameters
    ----------
    time
        An array of timestamps at which the instantaneous current was measured.
        Defaults to the :class:`pd.Index` of the :class:`pd.DataFrame`.

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

    dQ = I * dt

    if any([isinstance(i.m, UFloat) for i in dQ]):
        dQn, dQs, dQu = separate_data(dQ)
        Q = ureg.Quantity(unp.uarray(np.cumsum(dQn), dQs), dQu).to_base_units()
    else:
        Q = np.cumsum(dQ).to_base_units()

    ret = {output: Q}
    return ret


@load_data(
    ("time", "s", pd.Index),
    ("Q", "C"),
)
def average_current(
    time: pint.Quantity,
    Q: pint.Quantity,
    t0: pint.Quantity = None,
    output: str = "<I>",
) -> dict[str, pint.Quantity]:
    """
    Calculate the average current :math:`<I>` from a set of timestamped values of
    electical charge,

    .. math::

        <I> = \\frac{dQ}{dt} = \\frac{Q_n - Q_{n-1}}{t_n - t_{n-1}}

    where :math:`Q_n` is the charge and :math:`t_n` is the time at the :math:`n`-th
    datapoint.

    Parameters
    ----------
    time
        An array of timestamps at which the instantaneous current was measured.
        Defaults to the :class:`pd.Index` of the :class:`pd.DataFrame`.

    Q
        Values of the overall charge.

    t0
        An optional timestamp representing the time at which charge was zero. If not
        supplied, the first value in the ``time`` array will be used, with the charge
        at that timestamp set to zero.

    output
        Prefix of the columns where the calculated rate will be stored.


    Returns
    -------
    dict(output, I) : dict[str, pint.Quantity]
        Returns the average electrical current.

    """
    nts = len(time)
    if nts == 1 and t0 is not None:
        raise RuntimeError("A single timestep was provided without specifying 't0'.")
    elif t0 is not None:
        dt = np.diff(np.insert(time, 0, t0))
        dQ = np.diff(np.insert(Q, 0, ureg.Quantity(0, "C")))
    else:
        dt = np.diff(time)
        dQ = np.diff(Q)

    I = dQ / dt

    if len(I) != nts:
        I = np.insert(I, 0, ureg.Quantity(0, "A"))

    ret = {output: I}
    return ret
