import os
import pytest
import pandas as pd

from dgpost.transform import catalysis
from dgpost.utils import transform
from .utils import compare_dfs


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with floats
            "xinxout.float.df.pkl",
            [
                {"feedstock": "C3H8", "xin": "xin", "xout": "xout"},
            ],
            "Yp.float.pkl",
        ),
        (  # ts1 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {"feedstock": "propane", "element": "C", "xin": "xin", "xout": "xout"},
            ],
            "Yp.ufloat.pkl",
        ),
    ],
)
def test_yield_against_df(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        catalysis.catalytic_yield(df, **args)
    ref = pd.read_pickle(outpath)
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {"feedstock": "propane", "xin": "xin", "xout": "xout"},
            ],
            "Yp.ufloat.pkl",
        ),
    ],
)
def test_yield_with_transform(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    print(df.head())
    transform(df, "catalysis.catalytic_yield", using=spec)
    ref = pd.read_pickle(outpath)
    print(ref.head())
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "inpath, spec, outkeys",
    [
        (  # ts0 - dataframe with ufloats
            "catalysis.xlsx",
            [
                {"feedstock": "propane", "element": "C", "xin": "xin", "xout": "xout"},
            ],
            ["Yp_C->CO2", "Yp_C->CO", "Yp_C->C3H6"],
        ),
    ],
)
def test_yield_against_excel(inpath, spec, outkeys, datadir):
    os.chdir(datadir)
    df = pd.read_excel(inpath)
    transform(df, "catalysis.catalytic_yield", using=spec)
    for col in outkeys:
        pd.testing.assert_series_equal(df[col], df["r" + col], check_names=False)
