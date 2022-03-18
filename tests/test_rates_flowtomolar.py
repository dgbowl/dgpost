import os
import pytest
import pint
import pandas as pd
import uncertainties as uc

from dgpost.transform import rates

Trefs = [293.15, pint.Quantity(20, "degC"), uc.ufloat(293.15, 0.0)]


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - unit-naive dataframe with floats
            "flowcx.float.df.pkl",
            [
                {"flow": "flowin", "comp": "cin", "rate": "ndotin"},
                {"flow": "flowout", "comp": "xout", "rate": "ndotout"},
            ],
            "ndot.float.pkl",
        ),
        (  # ts1 - unit-naive dataframe with ufloats
            "flowcx.ufloat.df.pkl",
            [
                {"flow": "flowin", "comp": "cin", "rate": "ndotin"},
                {"flow": "flowout", "comp": "xout", "rate": "ndotout"},
            ],
            "ndot.ufloat.pkl",
        ),
        (  # ts2 - dataframe with units and floats
            "flowcx.units.float.df.pkl",
            [
                {"flow": "flowin", "comp": "cin", "rate": "ndotin"},
                {"flow": "flowout", "comp": "xout", "rate": "ndotout"},
            ],
            "ndot.units.float.pkl",
        ),
        (  # ts3 - dataframe with units and floats
            "flowcx.units.ufloat.df.pkl",
            [
                {"flow": "flowin", "comp": "cin", "rate": "ndotin"},
                {"flow": "flowout", "comp": "xout", "rate": "ndotout"},
            ],
            "ndot.units.ufloat.pkl",
        ),
        (  # ts4 - custom Tref
            "flowcx.units.ufloat.df.pkl",
            [
                {"flow": "flowin", "comp": "xout", "rate": "a"},
                {"flow": "flowin", "comp": "xout", "rate": "b", "Tref": Trefs[0]},
                {"flow": "flowin", "comp": "xout", "rate": "c", "Tref": Trefs[1]},
                {"flow": "flowin", "comp": "xout", "rate": "d", "Tref": Trefs[2]},
                {"flow": "flowin", "comp": "xout", "rate": "e", "Tref": "Tref"},
            ],
            "Tref.units.ufloat.pkl",
        ),
    ],
)
def test_cat_yield_floats(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        rates.flow_to_molar(df, **args)
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)
    assert ref.attrs == df.attrs
