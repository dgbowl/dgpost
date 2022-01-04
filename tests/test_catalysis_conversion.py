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
            "xinxout.df.pkl",
            [
                {"feedstock": "propane", "product": False},
                {"feedstock": "C3H8", "product": True, "element": "C"},
                {"feedstock": "O2", "product": False},
            ],
            "XpXr.float.pkl",
        ),
        (  # ts1 - dataframe with ufloats
            "xinxout.u.df.pkl",
            [
                {"feedstock": "propane", "product": False},
                {"feedstock": "C3H8", "product": True, "element": "C"},
                {"feedstock": "O2", "product": False},
            ],
            "XpXr.ufloat.pkl",
        ),
    ],
)
def test_cat_conv_floats(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    for args in spec:
        catalysis.conversion(df, **args)
    pd.to_pickle(df, f"C:\\Users\\krpe\\postprocess\\tests\\{outpath}")
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - dataframe with ufloats
            "xinxout.u.df.pkl",
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
