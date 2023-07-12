import os
import pytest
import pandas as pd
import numpy as np
import pint

from dgpost.transform import rates

from .utils import compare_dfs


@pytest.mark.parametrize(
    "spec, ref",
    [
        (  # ts0 - explicit t0, default units (s, mol/m3, m3)
            {
                "time": [1, 3, 4],
                "c": {"A": [10, 20, 25], "B": [5, 15, 16]},
                "V": 1,
                "t0": 0,
            },
            {
                "rate->A": pint.Quantity([10.0, 5.0, 5.0], "mol/s"),
                "rate->B": pint.Quantity([5.0, 5.0, 1.0], "mol/s"),
            },
        ),
        (  # ts1 - explicit units
            {
                "time": pint.Quantity([0, 1, 3, 4], "min"),
                "c": {
                    "A": pint.Quantity([0, 10, 20, 25], "mol/l"),
                    "B": pint.Quantity([0, 5, 15, 16], "mol/l"),
                },
                "V": pint.Quantity(1, "l"),
            },
            {
                "rate->A": pint.Quantity(
                    [np.NaN, 10.0 / 60, 5.0 / 60, 5.0 / 60], "mol/s"
                ),
                "rate->B": pint.Quantity(
                    [np.NaN, 5.0 / 60, 5.0 / 60, 1.0 / 60], "mol/s"
                ),
            },
        ),
    ],
)
def test_rates_batchtomolar_direct(spec, ref):
    ret = rates.batch_to_molar(**spec)
    for k, v in ref.items():
        assert np.allclose(v, ret[k], equal_nan=True)


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - unit-naive dataframe with floats
            "batchtomolar.plain.df.pkl",
            [
                {"V": "V", "c": "c"},
            ],
            "ref.batchtomolar.plain.df.pkl",
        ),
        (  # ts1 - unit-aware dataframe with floats
            "batchtomolar.units.df.pkl",
            [
                {"V": "V", "c": "c"},
            ],
            "ref.batchtomolar.units.df.pkl",
        ),
        (  # ts2 - unit-aware dataframe with floats, custom volume with units
            "batchtomolar.units.df.pkl",
            [
                {"V": pint.Quantity(0.05, "mm³"), "c": "c"},
            ],
            "ref.batchtomolar.units.df.pkl",
        ),
        (  # ts3 - unit-aware dataframe with floats, custom volume without units
            "batchtomolar.units.df.pkl",
            [
                {"V": 5e-11, "c": "c"},
            ],
            "ref.batchtomolar.units.df.pkl",
        ),
    ],
)
def test_rates_batchtomolar_df(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    for args in spec:
        df = rates.batch_to_molar(df, **args)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)
