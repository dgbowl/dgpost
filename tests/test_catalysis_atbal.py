import os
import pytest
import pandas as pd
import uncertainties as uc
from tests.utils import datadir

from dgpost.transform import catalysis
from dgpost.utils import transform


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with floats
            "xinxout.float.df.pkl",
            [
                {"element": "C"},
                {"element": "O"},
            ],
            "atbal.float.pkl",
        ),
        (  # ts1 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [{}],
            "atbal.ufloat.pkl",
        ),
        (  # ts2 - dataframe with units and floats
            "ndot.units.float.df.pkl",
            [
                {"element": "C", "xin": "nin", "xout": "nout"},
                {"element": "O", "xin": "nin", "xout": "nout"},
            ],
            "atbal.units.float.pkl",
        ),
        (  # ts3 - dataframe with units and ufloats
            "ndot.units.ufloat.df.pkl",
            [
                {"element": "C", "xin": "nin", "xout": "nout"},
                {"element": "O", "xin": "nin", "xout": "nout"},
            ],
            "atbal.units.ufloat.pkl",
        ),
    ],
)
def test_cat_atbal_floats(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        catalysis.atom_balance(df, **args)
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {"xin": "xin", "xout": "xout", "element": "C"},
            ],
            "atbal.ufloat.pkl",
        ),
    ],
)
def test_with_transform(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    transform(df, "catalysis.atom_balance", using=spec)
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)


@pytest.mark.parametrize(
    "inpath, spec, outkeys",
    [
        (  # ts0 - dataframe with ufloats
            "catalysis.xlsx",
            [
                {"element": "C"},
                {"element": "O"},
            ],
            ["atbal_C", "atbal_O"],
        ),
    ],
)
def test_against_excel(inpath, spec, outkeys, datadir):
    os.chdir(datadir)
    df = pd.read_excel(inpath)
    transform(df, "catalysis.atom_balance", using=spec)
    for col in outkeys:
        pd.testing.assert_series_equal(df[col], df["r" + col], check_names=False)
