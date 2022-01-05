import os
import pytest
import pandas as pd
import uncertainties as uc
import numpy as np
from tests.utils import datadir

from dgpost.transform import catalysis
from dgpost.utils import transform


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with floats
            "xinxout.float.df.pkl",
            [
                {"feedstock": "propane", "product": False},
                {"feedstock": "C3H8", "product": True, "element": "C"},
                {"feedstock": "O2", "product": False},
            ],
            "XpXr.float.pkl",
        ),
        (  # ts1 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {"feedstock": "propane", "product": False},
                {"feedstock": "C3H8", "product": True, "element": "C"},
                {"feedstock": "O2", "product": False},
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
def test_against_df(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        catalysis.conversion(df, **args)
    pd.to_pickle(df, f"C:\\Users\\krpe\\postprocess\\tests\\{outpath}")
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)
    assert ref.attrs == df.attrs


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with ufloats
            "xinxout.ufloat.df.pkl",
            [
                {"feedstock": "propane", "product": False},
                {"feedstock": "C3H8", "product": True, "element": "C"},
                {"feedstock": "O2", "product": False},
            ],
            "XpXr.ufloat.pkl",
        ),
    ],
)
def test_with_transform(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        transform(df, "catalysis.conversion", using=args)
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)
    assert ref.attrs == df.attrs


@pytest.mark.parametrize(
    "inpath, spec, outkeys",
    [
        (  # ts0 - dataframe with ufloats
            "catalysis.xlsx",
            [
                {"feedstock": "propane", "product": True, "element": "C"},
                {"feedstock": "oxygen"},
                {"feedstock": "C3H8", "product": False},
                {"feedstock": "O2", "product": False},
            ],
            ["Xr->C3H8", "Xr->O2", "Xp_C->propane", "Xp_O->oxygen"],
        ),
    ],
)
def test_against_excel(inpath, spec, outkeys, datadir):
    os.chdir(datadir)
    df = pd.read_excel(inpath)
    for args in spec:
        transform(df, "catalysis.conversion", using=args)
    for col in outkeys:
        pd.testing.assert_series_equal(df[col], df["r" + col], check_names=False)
