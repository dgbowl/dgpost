import os
import pytest
import pandas as pd
import numpy as np

from dgpost.transform import catalysis
from dgpost.utils import transform
from .utils import compare_dfs


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with floats
            "xinxout.float.df.pkl",
            [
                {"feedstock": "C3H8", "element": "C", "xout": "xout"},
                {"feedstock": "O2", "element": "O", "xout": "xout"},
            ],
            "Sp.float.pkl",
        ),
        (  # ts1 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {"feedstock": "propane", "element": "C", "xout": "xout"},
                {"feedstock": "O2", "element": "O", "xout": "xout"},
            ],
            "Sp.ufloat.pkl",
        ),
        (  # ts2 - dataframe with floats, elements implicit
            "xinxout.float.df.pkl",
            [
                {"feedstock": "C3H8", "xout": "xout"},
                {"feedstock": "O2", "xout": "xout"},
            ],
            "Sp.float.pkl",
        ),
        (  # ts3 - dataframe with units and floats
            "ndot.units.float.df.pkl",
            [
                {"feedstock": "propane", "xout": "nout"},
                {"feedstock": "O2", "xout": "nout"},
            ],
            "Sp.units.float.pkl",
        ),
        (  # ts4 - dataframe with units and ufloats
            "ndot.units.ufloat.df.pkl",
            [
                {"feedstock": "propane", "xout": "nout"},
                {"feedstock": "O2", "xout": "nout"},
            ],
            "Sp.units.ufloat.pkl",
        ),
        (  # ts5 - dataframe with nans
            "catalysis.nan.pkl",
            [
                {"feedstock": "CO2", "xout": "nout"},
            ],
            "ref.selectivity.nan.pkl",
        ),
    ],
)
def test_catalysis_selectivity_df(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        df = catalysis.selectivity(df, **args)
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
                {"feedstock": "propane", "element": "C", "xout": "xout"},
                {"feedstock": "O2", "element": "O", "xout": "xout"},
            ],
            "Sp.ufloat.pkl",
        )
    ],
)
def test_catalysis_selectivity_transform(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    df = transform(df, "catalysis.selectivity", using=spec)
    ref = pd.read_pickle(outpath)
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "inpath, spec, outkeys",
    [
        (  # ts0 - dataframe with ufloats
            "catalysis.xlsx",
            [{"feedstock": "propane", "element": "C", "xout": "xout"}],
            ["Sp_C", "Sp_C", "Sp_C"],
        ),
    ],
)
def test_catalysis_selectivity_excel(inpath, spec, outkeys, datadir):
    os.chdir(datadir)
    df = pd.read_excel(inpath)
    df = transform(df, "catalysis.selectivity", using=spec)
    for col in outkeys:
        compare_dfs(df[f"r{col}"], df[col])


def test_catalysis_selectivity_rinxin(datadir):
    os.chdir(datadir)
    df = pd.read_pickle("rinxin.pkl")
    df = catalysis.selectivity(df, feedstock="CH4", xout="xout", output="Sp1")
    df = catalysis.selectivity(df, feedstock="CH4", rout="nout", output="Sp2")
    df["nout->CH4"] = 0
    df = catalysis.selectivity(df, feedstock="CH4", rout="nout", output="Sp3")
    for col in ["Sp1", "Sp2", "Sp3"]:
        assert np.allclose(df[col]["CO"], np.array([0.2, 0.1, 0.1, 0.1, 0.1, 0.1]))
        assert np.allclose(df[col]["CO2"], np.array([0.8, 0.9, 0.9, 0.9, 0.9, 0.9]))
