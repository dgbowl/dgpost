import os
import pytest
import pandas as pd
import numpy as np
from uncertainties import ufloat
from uncertainties import unumpy as unp
import pint

from dgpost.transform import table
from .utils import compare_dfs


@pytest.mark.parametrize(
    "column, abs, rel, output",
    [
        (  # ts0 - strip uncertainty
            pint.Quantity(ufloat(6.0, 0.1), "l/h"),
            None,
            None,
            {"output": pint.Quantity(6.0, "l/h")},
        ),
        (  # ts1 - absolute uncertainty
            pint.Quantity(6.0, "l/h"),
            pint.Quantity(0.1, "l/h"),
            None,
            {"output": pint.Quantity(ufloat(6.0, 0.1), "l/h")},
        ),
        (  # ts2 - absolute uncertainty with different units
            pint.Quantity(6.0, "l/h"),
            pint.Quantity(1.0, "ml/min"),
            None,
            {"output": pint.Quantity(ufloat(6.0, 0.06), "l/h")},
        ),
        (  # ts3 - relative uncertainty without units
            pint.Quantity(6.0, "l/h"),
            None,
            0.1,
            {"output": pint.Quantity(ufloat(6.0, 0.6), "l/h")},
        ),
        (  # ts4 - relative uncertainty with units
            pint.Quantity(6.0, "l/h"),
            None,
            pint.Quantity(0.1, ""),
            {"output": pint.Quantity(ufloat(6.0, 0.6), "l/h")},
        ),
        (  # ts5 - both replace 1
            pint.Quantity(ufloat(100.0, 0.1), "ml/s"),
            pint.Quantity(8, "ml/s"),
            pint.Quantity(0.1, ""),
            {"output": pint.Quantity(ufloat(100.0, 10.0), "ml/s")},
        ),
        (  # ts6 - both replace 2
            pint.Quantity(ufloat(100.0, 0.1), "ml/s"),
            pint.Quantity(8, "ml/s"),
            pint.Quantity(0.05, ""),
            {"output": pint.Quantity(ufloat(100.0, 8.0), "ml/s")},
        ),
        (  # ts7 - with arrays
            pint.Quantity(unp.uarray([100, 90, 80, 70], [0.1, 0.1, 0.1, 0.1]), "ml/s"),
            pint.Quantity(8, "ml/s"),
            pint.Quantity(0.1, ""),
            {
                "output": pint.Quantity(
                    unp.uarray([100, 90, 80, 70], [10, 9, 8, 8]), "ml/s"
                )
            },
        ),
    ],
)
def test_table_set_uncertainty_column_direct(column, abs, rel, output):
    ret = table.set_uncertainty(column=column, abs=abs, rel=rel)
    for k, v in ret.items():
        for func in {unp.nominal_values, unp.std_devs}:
            assert np.allclose(func(output[k].m), func(v.m), equal_nan=True)


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - uncertainty with units
            "flowcx.units.ufloat.df.pkl",
            [{"column": "cin->C3H8", "abs": pint.Quantity(1, "mmol/l"), "rel": None}],
            "ts0.flowcx.units.ufloat.df.pkl",
        ),
        (  # ts1 - uncertainty without units
            "flowcx.units.ufloat.df.pkl",
            [{"column": "cin->C3H8", "abs": 0.001, "rel": None}],
            "ts0.flowcx.units.ufloat.df.pkl",
        ),
        (  # ts2 - strip namespace uncertainty
            "flowcx.units.ufloat.df.pkl",
            [{"namespace": "cin", "abs": None, "rel": None}],
            "ts2.flowcx.units.ufloat.df.pkl",
        ),
        (  # ts3 - correct uncertainty resolution
            "flowcx.units.ufloat.df.pkl",
            [
                {
                    "namespace": "xout",
                    "abs": pint.Quantity(100 / 1e6, ""),
                    "rel": pint.Quantity(1 / 100, ""),
                }
            ],
            "ts3.flowcx.units.ufloat.df.pkl",
        ),
    ],
)
def test_table_set_uncertainty_df(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    for args in spec:
        df = table.set_uncertainty(df, **args)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)
