import os
import pytest
from dgpost.transform import electrochemistry
import numpy as np
import pandas as pd
import pint

from .utils import compare_dfs


@pytest.mark.parametrize(
    "inputs, output",
    [
        (  # ts0 - pH, all floats
            {
                "Ewe": -3.09,
                "Eref": 0.197,
                "R": 14.7,
                "I": 0.1,
                "T": 298.15,
                "pH": 8.5,
            },
            {"Eapp": pint.Quantity(-0.9201455, "volt")},
        ),
        (  # ts1 - pH, all Quantities, default T = 298.15 K
            {
                "Ewe": pint.Quantity(np.array([-3.09, -3.09]), "volt"),
                "Eref": pint.Quantity(np.array([0.197, 0.197]), "volt"),
                "R": pint.Quantity(np.array([14.7, 14.7]), "ohm"),
                "I": pint.Quantity(np.array([100, 100]), "mA"),
                "pH": 8.5,
            },
            {"Eapp": pint.Quantity(np.array([-0.9201455, -0.9201455]), "volt")},
        ),
        (  # ts2 - pH, all np.ndarrays, no Eref
            {
                "Ewe": np.asarray([-3.09, -3.09]),
                "R": np.asarray([14.7, 14.7]),
                "I": np.asarray([0.1, 0.1]),
                "pH": 8.5,
            },
            {"Eapp": pint.Quantity(np.array([-1.1171455, -1.1171455]), "volt")},
        ),
        (  # ts3 - n and Q, all floats,
            {"Ewe": -3.09, "n": 1, "Q": 10 ** (-8.5), "output": "E"},
            {"E": pint.Quantity(-2.5871455, "volt")},
        ),
        (  # ts4 - Francesco's data
            {
                "Ewe": pint.Quantity(-3.42246, "volt"),
                "R": pint.Quantity(0.997466, "ohm"),
                "Eref": pint.Quantity(0.197, "volt"),
                "I": pint.Quantity(-199.919, "milliampere"),
            },
            {"Eapp": pint.Quantity(-3.02605, "volt")},
        ),
    ],
)
def test_electrochemistry_nernst_direct(inputs, output):
    n = inputs.get("output", "Eapp")
    ret = electrochemistry.nernst(**inputs)
    assert np.allclose(ret[n], output[n])


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - plain pd.DataFrame without units
            "electrochemistry_nernst.ts0.pkl",
            [{"Ewe": "Ewe", "Eref": "Eref", "R": "R", "I": "I", "pH": "pH"}],
            "ref.electrochemistry_nernst.ts0.pkl",
        ),
        (  # ts1 - unit-aware pd.DataFrame
            "electrochemistry_nernst.ts1.pkl",
            [{"Ewe": "Ewe", "Eref": "Eref", "R": "R", "I": "I", "pH": "pH"}],
            "ref.electrochemistry_nernst.ts1.pkl",
        ),
        (  # ts2 - unit-aware pd.DataFrame with ufloats
            "electrochemistry_nernst.ts2.pkl",
            [
                {
                    "Ewe": "Ewe",
                    "Eref": "Eref",
                    "R": "resistance",
                    "I": "current",
                    "pH": "pH",
                }
            ],
            "ref.electrochemistry_nernst.ts2.pkl",
        ),
    ],
)
def test_electrochemistry_nernst_df(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    for args in spec:
        df = electrochemistry.nernst(df, **args)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)
