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
                {
                    "feedstock": "propane",
                    "xin": "xin",
                    "xout": "xout",
                    "product": False,
                },
                {
                    "feedstock": "C3H8",
                    "xin": "xin",
                    "xout": "xout",
                    "product": True,
                    "element": "C",
                },
                {
                    "feedstock": "O2",
                    "xin": "xin",
                    "xout": "xout",
                    "product": False,
                },
            ],
            "XpXr.float.pkl",
        ),
        (  # ts1 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {
                    "feedstock": "propane",
                    "xin": "xin",
                    "xout": "xout",
                    "product": False,
                },
                {
                    "feedstock": "C3H8",
                    "xin": "xin",
                    "xout": "xout",
                    "product": True,
                    "element": "C",
                },
                {
                    "feedstock": "O2",
                    "xin": "xin",
                    "xout": "xout",
                    "product": False,
                },
            ],
            "XpXr.ufloat.pkl",
        ),
        (  # ts2 - dataframe with units and floats
            "ndot.units.float.df.pkl",
            [
                {"feedstock": "propane", "xin": "nin", "xout": "nout"},
                {"feedstock": "O2", "xin": "nin", "xout": "nout", "product": False},
            ],
            "XpXr.units.float.pkl",
        ),
        (  # ts3 - dataframe with units and ufloats
            "ndot.units.ufloat.df.pkl",
            [
                {"feedstock": "propane", "xin": "nin", "xout": "nout"},
                {"feedstock": "O2", "xin": "nin", "xout": "nout", "product": False},
            ],
            "XpXr.units.ufloat.pkl",
        ),
    ],
)
def test_conversion_against_df(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        catalysis.conversion(df, **args)
    ref = pd.read_pickle(outpath)
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {
                    "feedstock": "propane",
                    "xin": "xin",
                    "xout": "xout",
                    "product": False,
                },
                {
                    "feedstock": "C3H8",
                    "xin": "xin",
                    "xout": "xout",
                    "product": True,
                    "element": "C",
                },
                {
                    "feedstock": "O2",
                    "xin": "xin",
                    "xout": "xout",
                    "product": False,
                },
            ],
            "XpXr.ufloat.pkl",
        ),
    ],
)
def test_conversion_with_transform(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    transform(df, "catalysis.conversion", using=spec)
    ref = pd.read_pickle(outpath)
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "inpath, spec, outkeys",
    [
        (  # ts0 - dataframe with ufloats
            "catalysis.xlsx",
            [
                {
                    "feedstock": "propane",
                    "xin": "xin",
                    "xout": "xout",
                    "product": True,
                    "element": "C",
                },
                {
                    "feedstock": "oxygen",
                    "xin": "xin",
                    "xout": "xout",
                },
                {
                    "feedstock": "C3H8",
                    "xin": "xin",
                    "xout": "xout",
                    "product": False,
                },
                {
                    "feedstock": "O2",
                    "xin": "xin",
                    "xout": "xout",
                    "product": False,
                },
            ],
            ["Xr->C3H8", "Xr->O2", "Xp_C->propane", "Xp_O->oxygen"],
        ),
    ],
)
def test_conversion_against_excel(inpath, spec, outkeys, datadir):
    os.chdir(datadir)
    df = pd.read_excel(inpath)
    transform(df, "catalysis.conversion", using=spec)
    for col in outkeys:
        pd.testing.assert_series_equal(df[col], df["r" + col], check_names=False)
