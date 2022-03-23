"""
Module of transformations for chemical species rates.

"""
import pint

from dgpost.transform.helpers import load_data
from yadg.dgutils import ureg


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
    Tref: pint.Quantity = ureg.Quantity(273.15, "K"),
    pref: pint.Quantity = ureg.Quantity(1, "atm"),
    output="rate",
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
    df
        A pandas dataframe.

    flow
        Column containing the total flow.

    comp
        Prefix of the columns determining the flow composition.

    rate
        Prefix of the columns where the calculated rate will be stored.

    Tref
        Reference temperature of the flow measurement, used when ``comp`` is a mol
        fraction. Can be a column name or a numerical value in Kelvin; by default
        set to 0°C.

    pref
        Reference pressure of the flow measurement, used when ``comp`` is a mol
        fraction. Can be a column name or a numerical value in Pa; by default set
        to 1 atm.

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
