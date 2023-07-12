import os
import pytest
from dgpost.transform import electrochemistry, rates
import numpy as np
import pandas as pd
import pint

from .utils import compare_dfs


@pytest.mark.parametrize(
    "inputs, output",
    [
        (  # ts0 - all floats, default units of rate in mol/s
            {
                "I": 0.1,
                "rate": {
                    "H2": 1.89208726e-07,
                    "CH4": 3.15196823e-08,
                    "C2H4": 6.64130464e-09,
                },
                "charges": {"C": 4, "H": 1, "O": -2},
            },
            {
                "fe->H2": pint.Quantity(0.36511734),
                "fe->CH4": pint.Quantity(0.24329496),
                "fe->C2H4": pint.Quantity(0.07689462),
            },
        ),
        (  # ts1 - all Quantities, weird units
            {
                "I": pint.Quantity(100, "mA"),
                "rate": {
                    "H2": pint.Quantity(0.6811524, "mmol/hour"),
                    "CH4": pint.Quantity(0.1134709, "mmol/hour"),
                    "C2H4": pint.Quantity(0.0239087, "mmol/hour"),
                    "CO": pint.Quantity(0.0533184, "mmol/hour"),
                },
                "charges": {"C": 4, "H": 1, "O": -2},
            },
            {
                "fe->H2": pint.Quantity(0.36511734),
                "fe->CH4": pint.Quantity(0.24329496),
                "fe->C2H4": pint.Quantity(0.07689462),
                "fe->CO": pint.Quantity(0.02858024),
            },
        ),
        (  # ts2 - arrays, with I == 0, all Quantities, weird units
            {
                "I": pint.Quantity([0, 100], "mA"),
                "rate": {
                    "H2": pint.Quantity([0.6811524, 0.6811524], "mmol/hour"),
                    "CH4": pint.Quantity([0.1134709, 0.1134709], "mmol/hour"),
                    "C2H4": pint.Quantity([0.0239087, 0.0239087], "mmol/hour"),
                    "CO": pint.Quantity([0.0533184, 0.0533184], "mmol/hour"),
                },
                "charges": {"C": 4, "H": 1, "O": -2},
            },
            {
                "fe->H2": pint.Quantity([np.NaN, 0.36511734]),
                "fe->CH4": pint.Quantity([np.NaN, 0.24329496]),
                "fe->C2H4": pint.Quantity([np.NaN, 0.07689462]),
                "fe->CO": pint.Quantity([np.NaN, 0.02858024]),
            },
        ),
    ],
)
def test_electrochemistry_fe_direct(inputs, output):
    tag = inputs.get("output", "fe")
    ret = electrochemistry.fe(**inputs)
    print(ret)
    for k in inputs["rate"].keys():
        n = f"{tag}->{k}"
        assert np.allclose(ret[n], output[n], equal_nan=True)


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - real world data from 2022_02_22
            "2022_02_22.df.GC+flow+I.pkl",
            [
                {
                    "flow": "fout",
                    "x": "xout",
                    "output": "nout",
                    "Tref": pint.Quantity(0, "degC"),
                    "pref": pint.Quantity(1, "atm"),
                },
                {
                    "I": "I",
                    "rate": "nout",
                    "charges": {"C": 4, "H": 1, "O": -2},
                },
            ],
            "ref.electrochemistry_fe.ts0.pkl",
        )
    ],
)
def test_electrochemistry_fe_df(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    df = rates.flow_to_molar(df, **spec[0])
    df = electrochemistry.fe(df, **spec[1])
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)
