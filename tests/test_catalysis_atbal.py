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
                {"element": "C", "xin": "xin", "xout": "xout"},
                {"element": "O", "xin": "xin", "xout": "xout"},
            ],
            "atbal.float.pkl",
        ),
        (  # ts1 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [{"xin": "xin", "xout": "xout"}],
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
def test_catalysis_atbal_df(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        df = catalysis.atom_balance(df, **args)
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
                {"xin": "xin", "xout": "xout", "element": "C"},
            ],
            "atbal.ufloat.pkl",
        ),
    ],
)
def test_catalysis_atbal_transform(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    df = transform(df, "catalysis.atom_balance", using=spec)
    ref = pd.read_pickle(outpath)
    df.to_pickle(outpath)
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "inpath, spec, outkeys",
    [
        (  # ts0 - dataframe with ufloats
            "catalysis.xlsx",
            [
                {"element": "C", "xin": "xin", "xout": "xout"},
                {"element": "O", "xin": "xin", "xout": "xout"},
            ],
            ["atbal_C", "atbal_O"],
        ),
    ],
)
def test_catalysis_atbal_excel(inpath, spec, outkeys, datadir):
    os.chdir(datadir)
    df = pd.read_excel(inpath)
    df = transform(df, "catalysis.atom_balance", using=spec)
    for col in outkeys:
        pd.testing.assert_frame_equal(df[col], df[f"r{col}"], check_names=False)


def test_catalysis_atbal_rinxin(datadir):
    os.chdir(datadir)
    df = pd.read_pickle("rinxin.pkl")
    df = catalysis.atom_balance(df, xin="xin", xout="xout", element="C", output="C1")
    df = catalysis.atom_balance(df, rin="nin", rout="nout", element="C", output="C2")
    df = catalysis.atom_balance(df, xin="xin", xout="xout", element="O", output="O1")
    df = catalysis.atom_balance(df, rin="nin", rout="nout", element="O", output="O2")
    assert np.allclose(df["C1"], pd.DataFrame([1.0, 1.0, 0.995, 1.005, 1.01, 0.99]))
    assert np.allclose(df["C2"], pd.DataFrame([1.0, 1.0, 0.995, 1.005, 1.01, 0.99]))
    assert np.allclose(df["O1"], pd.DataFrame([1.0, 1.0, 0.95, 1.05, 1.0, 1.0]))
    assert np.allclose(df["O2"], pd.DataFrame([1.0, 1.0, 0.95, 1.05, 1.0, 1.0]))
