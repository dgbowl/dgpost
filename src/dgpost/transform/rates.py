"""
.. codeauthor::
    Peter Kraus

Includes functions to convert mixture compositions (concentration, mol fraction)
from instantaneous flow data or continuous batch data to rates (dimension of
``[quantity]/[time]``). The :func:`~dgpost.transform.rates.flow_to_molar` function
is useful for converting gas-phase or liquid flows, while
:func:`~dgpost.transform.rates.batch_to_molar` can be used to determine formation
rates from the concentration profile of a batch mixture.

.. rubric:: Functions

.. autosummary::

    batch_to_molar
    flow_to_molar

"""
import pint
import pandas as pd
import numpy as np
from typing import Iterable

from dgpost.utils.helpers import load_data

ureg = pint.get_application_registry()


@load_data(
    ("flow", "m³/s"),
    ("c", "mol/m³", dict),
    ("x", None, dict),
    ("Tref", "K"),
    ("pref", "Pa"),
)
def flow_to_molar(
    flow: pint.Quantity,
    c: dict[str, pint.Quantity] = None,
    x: dict[str, pint.Quantity] = None,
    Tref: pint.Quantity = pint.Quantity(273.15, "K"),
    pref: pint.Quantity = pint.Quantity(1, "atm"),
    output: str = "rate",
) -> dict[str, pint.Quantity]:
    """
    Calculates a molar rate of species from specified flow and composition. The
    units of the rate have to be either dimensionless (for unit-naive dataframes) or
    in dimensions of [substance]/[time].

    Currently, three combinations of units are supported:

     - Dimensionless ``flow`` and dimensionless ``comp``, as is the case for unit-naive
       dataframes. In this case, the molar flow rates of species :math:`r_s` are
       calculated by a simple multiplication:

       .. math::

            r_s = \\text{flow} \\times \\text{comp}_s

     - Volumetric ``flow`` :math:`\\dot{V}` and composition ``comp`` as a concentration,
       as is often the case in liquid flows. In this case, the molar rates of species
       :math:`r_s` are also a simple multiplication (accounting for unit conversion):

       .. math::

            r_s = \\dot{V} \\times c_s

     - Volumetric ``flow`` :math:`\\dot{V}` and composition ``comp`` as a dimensionless
       molar fraction :math:`x_s`, in which case the flow is assumed to be gas-phase. In
       this case, the flow has to be converted to molar units using the ideal gas law:

       .. math::

           r_s = \\dot{V} \\times \\frac{p_\\text{ref}}{RT_\\text{ref}} \\times x_s

       The pressure :math:`p_\\text{ref}` and temperature :math:`T_\\text{ref}` are
       specifying the state at which the flow :math:`\\dot{V}` has been measured.

    Parameters
    ----------
    flow
        The total flow of the mixture.

    c
        A dictionary containing the composition of the mixture as concentration.
        Cannot be supplied at the same time as ``x``.

    x
        A dictionary containing the composition of the mixture as mole fraction.
        Assuming ideal gas-phase flow. Cannot be supplied at the same time as ``c``.

    Tref
        Reference temperature of the flow measurement, used when composition is
        specified using a mol fraction. By default set to 273.15 K.

    pref
        Reference pressure of the flow measurement, used when composition is
        specified using a mol fraction. By default set to 1 atm.

    output
        Prefix of the keys of the returned rate dictionary.

    """
    if x is not None and c is not None:
        raise RuntimeError("Cannot supply both concentration 'c' and mole fraction 'x'")
    elif c is not None:
        ret = {}
        for k, v in c.items():
            r = flow * v
            ret[f"{output}->{k}"] = r.to_base_units()
    elif x is not None:
        ret = {}
        for k, v in x.items():
            r = flow * (pref / (ureg("molar_gas_constant") * Tref.to("K"))) * v
            ret[f"{output}->{k}"] = r.to_base_units()

    return ret


@load_data(
    ("time", "s", pd.Index),
    ("c", "mol/m³", dict),
    ("V", "m³"),
)
def batch_to_molar(
    time: pint.Quantity,
    c: dict[str, pint.Quantity],
    V: pint.Quantity,
    t0: pint.Quantity = None,
    output: str = "rate",
) -> dict[str, pint.Quantity]:
    """
    Calculates a molar rate of species from specified volume and composition at
    the specified timesteps. The units of the rate have to be either dimensionless
    (for unit-naive dataframes) or in dimensions of [substance]/[time].

    First, the :math:`\\delta t` and :math:`\\delta c(x)` at each timestep :math:`n` is
    calculated:

    .. math::

        \\delta t_n = t_n - t_{n-1}
        \\delta c(x)_n = c(x)_n - c(x)_{n-1}

    Then, the formation rate is calculated using the volume:

    .. math:

        \\text{rate}(x)_n = V_n \\frac{\\delta c(x)_n}{\\delta t_n}


    Parameters
    ----------
    time
        An array of timestamps at which the concentrations and volumes are measured.

    c
        A dictionary containing concentrations of species at the specified timestamps.

    V
        Volume of the batch at the timestamps.

    t0
        An optional timestamp representing the initial time where all concentrations
        are zero. If not supplied, the calculation will use the first datapoint as
        reference with its rates set to zero.

    output
        Prefix of the columns where the calculated rate will be stored.

    """
    nts = len(time)
    if nts == 1 and t0 is not None:
        raise RuntimeError("A single timestep was provided without specifying 't0'.")
    elif t0 is not None:
        time = np.insert(time, 0, t0)
        c0 = ureg.Quantity(0, "mol/m³")
        for k, v in c.items():
            c[k] = np.insert(v, 0, c0)
    elif isinstance(V.m, Iterable) and len(V) == nts:
        V = V[1:]

    dt = np.diff(time)
    dc = {k: np.diff(v) for k, v in c.items()}
    ret = {}
    for k, dc_k in dc.items():
        r = (dc_k / dt) * V
        if len(r) < nts:
            r0 = ureg.Quantity(np.nan, "mol/s")
            r = np.insert(r, 0, r0)
        ret[f"{output}->{k}"] = r.to_base_units()
    return ret
