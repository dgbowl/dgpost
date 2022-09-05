import os
import pytest
import pandas as pd
import numpy as np

from dgpost.transform import reflection
from dgpost.utils import transform
from .utils import compare_dfs

from yadg.dgutils import ureg


@pytest.mark.parametrize(
    "func, spec",
    [
        (  # ts0 - prune_cutoff defaults
            "prune_cutoff",
            [
                {
                    "freq": "freq",
                    "imag": "imag",
                    "real": "real",
                    "cutoff": 0.4,
                    "output": "S11",
                }
            ],
        ),
        (  # ts1 - prune_gradient defaults
            "prune_gradient",
            [
                {
                    "freq": "freq",
                    "imag": "imag",
                    "real": "real",
                    "threshold": 1e-6,
                    "output": "S11",
                }
            ],
        ),
    ],
)
def test_reflection_prune_df(func, spec, datadir):
    infile = "qftrace.pkl"
    outfile = f"ref.{func}.pkl"
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    df = transform(df, f"reflection.{func}", spec)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - fit_kajfez first peak
            "ref.prune_cutoff.pkl",
            [
                {
                    "freq": "S11(0)->freq",
                    "imag": "S11(0)->imag",
                    "real": "S11(0)->real",
                },
            ],
            "ref.fit_kajfez_0.pkl",
        ),
        (  # ts1 - fit_kajfez second peak
            "ref.prune_cutoff.pkl",
            [
                {
                    "freq": "S11(1)->freq",
                    "imag": "S11(1)->imag",
                    "real": "S11(1)->real",
                },
            ],
            "ref.fit_kajfez_1.pkl",
        ),
        (  # ts2 - prune and fit fit
            "pruned.2.pkl",
            [
                {
                    "freq": "pruned(0)->freq",
                    "imag": "pruned(0)->imag",
                    "real": "pruned(0)->real",
                    "output": "S11(0)",
                },
                {
                    "freq": "pruned(1)->freq",
                    "imag": "pruned(1)->imag",
                    "real": "pruned(1)->real",
                    "output": "S11(1)",
                },
            ],
            "ref.fit_kajfez_2.pkl",
        ),
    ],
)
def test_reflection_fit_kajfez_df(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    df = transform(df, "reflection.qf_kajfez", spec)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)
