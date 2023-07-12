import os
import pytest
import pandas as pd
import numpy as np
import pint

from dgpost.transform import electrochemistry

from .utils import compare_dfs


@pytest.mark.parametrize(
    "spec, ref",
    [
        (  # ts0 - explicit t0, constant I, default units
            {
                "time": [1, 2, 4, 5, 7, 8],
                "I": 0.1,
                "t0": 0,
            },
            {
                "Q": pint.Quantity([0.1, 0.2, 0.4, 0.5, 0.7, 0.8], "A s"),
            },
        ),
        (  # ts1 - variable I, custom units
            {
                "time": pint.Quantity([0.1, 0.2, 0.4, 0.5, 0.7, 0.8], "h"),
                "I": pint.Quantity([100, 99, 99, 100, 100, 98], "mA"),
            },
            {
                "Q": pint.Quantity([0.0, 9.9, 29.7, 39.7, 59.7, 69.5], "mAh"),
            },
        ),
    ],
)
def test_electrochemistry_charge_direct(spec, ref):
    ret = electrochemistry.charge(**spec)
    for k, v in ref.items():
        assert np.allclose(v, ret[k])


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - real world data from 2022_02_22
            "2022_02_22.df.GC+flow+I.pkl",
            {"I": "I", "output": "Qtot"},
            "ref.electrochemistry_charge.ts0.pkl",
        )
    ],
)
def test_electrochemistry_charge_df(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    df = electrochemistry.charge(df, **spec)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)
