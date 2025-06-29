import os
import numpy as np
import pandas as pd

from dgpost.transform import mixtures


def test_rates_flowtofraction_pkl(datadir):
    os.chdir(datadir)
    df = pd.read_pickle("ftot.pkl")
    df = mixtures.flows_to_fractions(df, total="ftot", vdot="f", output="x")
    print(f"{df=}")
    assert np.allclose(df[("x", "a")], df[("xref", "a")])
    assert np.allclose(df[("x", "b")], df[("xref", "b")])


def test_rates_flowtofraction_nan(datadir):
    os.chdir(datadir)
    df = pd.read_pickle("ftot.nan.pkl")
    df = mixtures.flows_to_fractions(df, total="ftot", vdot="f", output="x")
    print(f"{df=}")
    assert np.allclose(df[("x", "a")], df[("xref", "a")], equal_nan=True)
    assert np.allclose(df[("x", "b")], df[("xref", "b")], equal_nan=True)
