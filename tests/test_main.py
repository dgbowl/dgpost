import pytest
import yadg.core
import json
import os
import pandas as pd
import numpy as np
from uncertainties import unumpy as unp
import uncertainties as uc

from tests.utils import datadir
import dgpost


@pytest.mark.parametrize(
    "inpath, tname, outpath",
    [
        (  # ts0 - load 1 dg, extract 2 keys directly
            "le_1.yaml",
            "table 1",
            "le_1.pkl",
        ),
        (  # ts1 - load 2 dgs, extract 2 tables with interpolation
            "le_2.yaml",
            "table 2",
            "le_2.pkl",
        ),
        (  # ts2 - load & extract, transform using catalysis.conversion
            "let_1.yaml",
            "df",
            "let_1.pkl",
        ),
        (  # ts3 - load & extract, multiple transforms
            "let_2.yaml",
            "df",
            "let_2.pkl",
        ),
        (  # ts4 - load & double extract, same index
            "lee_1.yaml",
            "df",
            "lee_1.pkl",
        ),
    ],
)
def test_run(inpath, tname, outpath, datadir):
    os.chdir(datadir)
    dg, tab = dgpost.run(inpath)
    df = tab[tname]
    print(df.head())
    pd.to_pickle(df, f"C:\\Users\\krpe\\postprocess\\tests\\{outpath}")
    ref = pd.read_pickle(outpath)
    for col in df.columns:
        assert np.allclose(unp.nominal_values(ref[col]), unp.nominal_values(df[col]))
        assert np.allclose(unp.std_devs(ref[col]), unp.std_devs(df[col]))
    assert ref.attrs == df.attrs


@pytest.mark.parametrize(
    "inpath, tname, outpath",
    [
        (  # ts0 - load & double extract, different index
            "lee_2.yaml",
            "df",
            "lee_2.pkl",
        )
    ],
)
def test_run_withna(inpath, tname, outpath, datadir):
    os.chdir(datadir)
    dg, tab = dgpost.run(inpath)
    df = tab[tname]
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref.isna(), df.isna(), check_like=True)
    r = ref.fillna(uc.ufloat(0,0))
    t = df.fillna(uc.ufloat(0,0))
    pd.testing.assert_frame_equal(ref, df, check_like=True)
    assert ref.attrs == df.attrs
