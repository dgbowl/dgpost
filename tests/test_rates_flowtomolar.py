import os
import pytest
import pandas as pd
import numpy as np
import uncertainties as uc
import uncertainties.unumpy as unp

from yadg.dgutils import ureg
from dgpost.transform import rates

from .utils import compare_dfs

Trefs = [293.15, ureg.Quantity(20, "degC"), uc.ufloat(293.15, 0.0)]


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - unit-naive dataframe with floats
            "flowcx.float.df.pkl",
            [
                {"flow": "flowin", "c": "cin", "output": "ndotin"},
                {"flow": "flowout", "c": "xout", "output": "ndotout"},
            ],
            "ndot.float.pkl",
        ),
        (  # ts1 - unit-naive dataframe with ufloats
            "flowcx.ufloat.df.pkl",
            [
                {"flow": "flowin", "c": "cin", "output": "ndotin"},
                {"flow": "flowout", "c": "xout", "output": "ndotout"},
            ],
            "ndot.ufloat.pkl",
        ),
        (  # ts2 - dataframe with units and floats
            "flowcx.units.float.df.pkl",
            [
                {"flow": "flowin", "c": "cin", "output": "ndotin"},
                {"flow": "flowout", "x": "xout", "output": "ndotout"},
            ],
            "ndot.units.float.pkl",
        ),
        (  # ts3 - dataframe with units and floats
            "flowcx.units.ufloat.df.pkl",
            [
                {"flow": "flowin", "c": "cin", "output": "ndotin"},
                {"flow": "flowout", "x": "xout", "output": "ndotout"},
            ],
            "ndot.units.ufloat.pkl",
        ),
        (  # ts4 - custom Tref
            "flowcx.units.ufloat.df.pkl",
            [
                {"flow": "flowin", "x": "xout", "output": "a"},
                {"flow": "flowin", "x": "xout", "output": "b", "Tref": Trefs[0]},
                {"flow": "flowin", "x": "xout", "output": "c", "Tref": Trefs[1]},
                {"flow": "flowin", "x": "xout", "output": "d", "Tref": Trefs[2]},
                {"flow": "flowin", "x": "xout", "output": "e", "Tref": "Tref"},
            ],
            "Tref.units.ufloat.pkl",
        ),
    ],
)
def test_rates_flowtomolar_df(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    for args in spec:
        df = rates.flow_to_molar(df, **args)
    ref = pd.read_pickle(outfile)
    compare_dfs(ref, df)
