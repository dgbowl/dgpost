import os
import pytest
import pandas as pd

from dgpost.transform import catalysis
from dgpost.utils import transform


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with floats
            "xinxout.float.df.pkl",
            [{"feedstock": "C3H8"},],
            "Yp.float.pkl",
        ),
        (  # ts1 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [{"feedstock": "propane", "element": "C"},],
            "Yp.ufloat.pkl",
        ),
    ],
)
def test_cat_yield_floats(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        catalysis.catalytic_yield(df, **args)
    print(df.head())
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [{"feedstock": "propane"},],
            "Yp.ufloat.pkl",
        ),
    ],
)
def test_with_transform(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    transform(df, "catalysis.catalytic_yield", using=spec)
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)


@pytest.mark.parametrize(
    "inpath, spec, outkeys",
    [
        (  # ts0 - dataframe with ufloats
            "catalysis.xlsx",
            [{"feedstock": "propane", "element": "C"},],
            ["Yp_C->CO2", "Yp_C->CO", "Yp_C->C3H6"],
        ),
    ],
)
def test_against_excel(inpath, spec, outkeys, datadir):
    os.chdir(datadir)
    df = pd.read_excel(inpath)
    transform(df, "catalysis.catalytic_yield", using=spec)
    for col in outkeys:
        pd.testing.assert_series_equal(df[col], df["r" + col], check_names=False)
