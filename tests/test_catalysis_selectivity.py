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
                {"feedstock": "C3H8", "element": "C"},
                {"feedstock": "O2", "element": "O"},
            ],
            "Sp.float.pkl",
        ),
        (  # ts1 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {"feedstock": "propane", "element": "C"},
                {"feedstock": "O2", "element": "O"},
            ],
            "Sp.ufloat.pkl",
        ),
        (  # ts2 - dataframe with floats, elements implicit
            "xinxout.float.df.pkl",
            [{"feedstock": "C3H8"}, {"feedstock": "O2"},],
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
def test_against_df(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        catalysis.selectivity(df, **args)
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)
    assert ref.attrs == df.attrs


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {"feedstock": "propane", "element": "C"},
                {"feedstock": "O2", "element": "O"},
            ],
            "Sp.ufloat.pkl",
        )
    ],
)
def test_with_transform(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    transform(df, "catalysis.selectivity", using=spec)
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)
    assert ref.attrs == df.attrs


@pytest.mark.parametrize(
    "inpath, spec, outkeys",
    [
        (  # ts0 - dataframe with ufloats
            "catalysis.xlsx",
            [{"feedstock": "propane", "element": "C"},],
            ["Sp_C->CO2", "Sp_C->CO", "Sp_C->C3H6"],
        ),
    ],
)
def test_against_excel(inpath, spec, outkeys, datadir):
    os.chdir(datadir)
    df = pd.read_excel(inpath)
    transform(df, "catalysis.selectivity", using=spec)
    for col in outkeys:
        pd.testing.assert_series_equal(df[col], df["r" + col], check_names=False)
