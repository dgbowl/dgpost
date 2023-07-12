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
        (  # ts0 - default units, prepend zero
            {"time": [1, 2, 4, 5, 7, 8], "Q": [100, 90, 70, 60, 40, 30]},
            {
                "<I>": pint.Quantity([0, -10, -10, -10, -10, -10], "A"),
            },
        ),
        (  # ts1 - explicit t0, custom units
            {
                "time": pint.Quantity([0.1, 0.2, 0.4, 0.5, 0.7, 0.8], "h"),
                "Q": pint.Quantity([1, 2, 4, 5, 7, 8], "mAh"),
                "t0": 0.0,
                "output": "I",
            },
            {
                "I": pint.Quantity([10, 10, 10, 10, 10, 10], "mA"),
            },
        ),
    ],
)
def test_electrochemistry_current_direct(spec, ref):
    ret = electrochemistry.average_current(**spec)
    for k, v in ref.items():
        assert np.allclose(v, ret[k])


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - real world data from 2022_02_22
            "2022_02_22.df.GC+flow+I.pkl",
            [
                {"I": "I", "output": "Qtot"},
                {"Q": "Qtot"},
            ],
            "ref.electrochemistry_current.ts0.pkl",
        )
    ],
)
def test_electrochemistry_current_df(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    df = electrochemistry.charge(df, **spec[0])
    df = electrochemistry.average_current(df, **spec[1])
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)
