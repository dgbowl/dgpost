"""
Module of transformations for chemical species rates.

"""
import pandas as pd
import pint
from typing import Union

from dgpost.transform.helpers import pQ, save

def flow_to_molar(
    df: pd.DataFrame,
    flow: str,
    comp: str,
    rate: str,
    Tref: Union[str, float] = None,
    pref: Union[str, float] = None
) -> None:
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
    flow = pQ(df, flow)
    
    for col in df.columns:
        if col.startswith(comp):
            name = col.split("->")[1]
            x = pQ(df, col)
            
            # dimensionless flow:
            if flow.dimensionless:
                assert x.dimensionless, (
                    f"flow_to_rate: Provided 'flow' is dimensionless, "
                    f"but provided 'comp' element '{col}' is not: {x.u}."
                )
                r = flow * x
            # volumetric flow:
            elif flow.check('[volume]/[time]'):
                if x.check('[substance]/[volume]'):
                    r = flow * x
                elif x.dimensionless:
                    if isinstance(Tref, str):
                        RTref = pQ(df, Tref).to("K") * pint.Quantity(1, "R")
                    elif Tref is not None:
                        RTref = pint.Quantity(Tref, "kelvin") * pint.Quantity(1, "R")
                    else:
                        RTref = pint.Quantity(0, "degC").to("K") * pint.Quantity(1, "R")
                        
                    if isinstance(pref, str):
                        pref = pQ(df, pref)
                    elif pref is not None:
                        pref = pint.Quantity(pref, "pascal")
                    else:
                        pref = pint.Quantity(1, "atm")
                    
                    r = flow * (pref/(RTref)) * x
            
            tag = f"{rate}->{name}"
            save(df, tag, r)


            
                