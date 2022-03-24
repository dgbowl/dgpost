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
                {"feedstock": "C3H8", "element": "C", "xin": "xin", "xout": "xout"},
                {"feedstock": "O2", "element": "O", "xin": "xin", "xout": "xout"},
            ],
            "Sp.float.pkl",
        ),
        (  # ts1 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {"feedstock": "propane", "element": "C", "xin": "xin", "xout": "xout"},
                {"feedstock": "O2", "element": "O", "xin": "xin", "xout": "xout"},
            ],
            "Sp.ufloat.pkl",
        ),
        (  # ts2 - dataframe with floats, elements implicit
            "xinxout.float.df.pkl",
            [
                {"feedstock": "C3H8", "xin": "xin", "xout": "xout"},
                {"feedstock": "O2", "xin": "xin", "xout": "xout"},
            ],
            "Sp.float.pkl",
        ),
        (  # ts3 - dataframe with units and floats
            "ndot.units.float.df.pkl",
            [
                {"feedstock": "propane", "xin": "nin", "xout": "nout"},
                {"feedstock": "O2", "xin": "nin", "xout": "nout"},
            ],
            "Sp.units.float.pkl",
        ),
        (  # ts4 - dataframe with units and ufloats
            "ndot.units.ufloat.df.pkl",
            [
                {"feedstock": "propane", "xin": "nin", "xout": "nout"},
                {"feedstock": "O2", "xin": "nin", "xout": "nout"},
            ],
            "Sp.units.ufloat.pkl",
        ),
    ],
)
def test_selectivity_against_df(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        catalysis.selectivity(df, **args)
    ref = pd.read_pickle(outpath)
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {"feedstock": "propane", "element": "C", "xin": "xin", "xout": "xout"},
                {"feedstock": "O2", "element": "O", "xin": "xin", "xout": "xout"},
            ],
            "Sp.ufloat.pkl",
        )
    ],
)
def test_selectivity_with_transform(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    transform(df, "catalysis.selectivity", using=spec)
    ref = pd.read_pickle(outpath)
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "inpath, spec, outkeys",
    [
        (  # ts0 - dataframe with ufloats
            "catalysis.xlsx",
            [{"feedstock": "propane", "element": "C", "xin": "xin", "xout": "xout"}],
            ["Sp_C->CO2", "Sp_C->CO", "Sp_C->C3H6"],
        ),
    ],
)
def test_selectivity_against_excel(inpath, spec, outkeys, datadir):
    os.chdir(datadir)
    df = pd.read_excel(inpath)
    transform(df, "catalysis.selectivity", using=spec)
    for col in outkeys:
        pd.testing.assert_series_equal(df[col], df["r" + col], check_names=False)
