import os
import pytest
import pandas as pd
import numpy as np

from dgpost.transform import catalysis, rates
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
        (  # ts4 - dataframe with nans
            "catalysis.nan.pkl",
            [
                {"feedstock": "CO2", "rin": "nin", "rout": "nout", "type": "mixed"},
            ],
            "ref.conversion.nan.pkl",
        ),
    ],
)
def test_catalysis_conversion_df(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        df = catalysis.conversion(df, **args)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outpath)
    print(f"{ref.head()=}")
    df.to_pickle(outpath)
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
def test_catalysis_conversion_transform(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    df = transform(df, "catalysis.conversion", using=spec)
    ref = pd.read_pickle(outpath)
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "inpath, spec, outkeys",
    [
        (  # ts0
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
            ["Xr", "Xp_C", "Xp_O"],
        ),
        (  # ts1
            "molar_rates.xlsx",
            [
                {
                    "feedstock": "CO2",
                    "rin": "nin",
                    "rout": "nout",
                    "type": "mixed",
                    "element": "C",
                }
            ],
            ["Xm_C"],
        ),
    ],
)
def test_catalysis_conversion_excel(inpath, spec, outkeys, datadir):
    os.chdir(datadir)
    df = pd.read_excel(inpath)
    df = transform(df, "catalysis.conversion", using=spec)
    for col in outkeys:
        pd.testing.assert_frame_equal(df[col], df[f"r{col}"], check_names=False)


def test_catalysis_conversion_rinxin(datadir):
    os.chdir(datadir)
    df = pd.read_pickle("rinxin.pkl")
    df = catalysis.conversion(
        df, feedstock="CH4", xin="xin", xout="xout", type="reactant", output="Xr1"
    )
    df = catalysis.conversion(
        df, feedstock="CH4", rin="nin", rout="nout", type="reactant", output="Xr2"
    )
    df = catalysis.conversion(
        df, feedstock="CH4", xin="xin", xout="xout", type="product", output="Xp1"
    )
    df = catalysis.conversion(
        df, feedstock="CH4", rin="nin", rout="nout", type="product", output="Xp2"
    )
    df = catalysis.conversion(
        df, feedstock="CH4", xin="xin", xout="xout", standard="Ar", output="Xp3"
    )
    df = catalysis.conversion(
        df, feedstock="CH4", rin="nin", rout="nout", type="mixed", output="Xm1"
    )
    del df["nout"]["CH4"]
    df = catalysis.conversion(
        df, feedstock="CH4", rin="nin", rout="nout", type="mixed", output="Xm2"
    )
    for col in ["Xr1", "Xr2"]:
        assert np.allclose(
            df[col]["CH4"],
            np.array([0.05, 0.1, 0.1, 0.1, 0.091, 0.109]),
            atol=1e-6,
        ), f"Failed calculating {col}."
    for col in ["Xp1", "Xp2", "Xp3"]:
        assert np.allclose(
            df[col]["CH4"],
            np.array([0.05, 0.1, 0.095477, 0.104478, 0.1, 0.1]),
            atol=1e-6,
        ), f"Failed calculating {col}."
    for col in ["Xm1", "Xm2"]:
        assert np.allclose(
            df[col]["CH4"],
            np.array([0.05, 0.1, 0.095, 0.105, 0.101, 0.099]),
            atol=1e-6,
        ), f"Failed calculating {col}."
