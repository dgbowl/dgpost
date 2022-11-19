import os
import pytest
import pandas as pd
from yadg.dgutils import ureg
from dgpost.transform import chromatography
from .utils import compare_dfs


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - quantities
            "datasc.df.pkl",
            {
                "time": "time",
                "signal": "signal",
                "species": {
                    "CO": {
                        "l": ureg.Quantity(511.8, "s"),
                        "r": ureg.Quantity(521.4, "s"),
                    },
                    "methane": {
                        "l": ureg.Quantity(521.4, "s"),
                        "r": ureg.Quantity(526.8, "s"),
                    },
                    "CO2": {
                        "l": ureg.Quantity(529.2, "s"),
                        "r": ureg.Quantity(538.8, "s"),
                    },
                    "ethylene": {
                        "l": ureg.Quantity(541.8, "s"),
                        "r": ureg.Quantity(550.2, "s"),
                    },
                    "ethane": {
                        "l": ureg.Quantity(552.6, "s"),
                        "r": ureg.Quantity(558.0, "s"),
                    },
                    "propylene": {
                        "l": ureg.Quantity(595.2, "s"),
                        "r": ureg.Quantity(602.0, "s"),
                    },
                    "propane": {
                        "l": ureg.Quantity(602.0, "s"),
                        "r": ureg.Quantity(606.0, "s"),
                    },
                    "butane": {
                        "l": ureg.Quantity(690.0, "s"),
                        "r": ureg.Quantity(696.0, "s"),
                    },
                    "acetic": {
                        "l": ureg.Quantity(249.6, "s"),
                        "r": ureg.Quantity(260.4, "s"),
                    },
                    "acrylic": {
                        "l": ureg.Quantity(307.2, "s"),
                        "r": ureg.Quantity(318.0, "s"),
                    },
                },
                "output": "FID",
            },
            "FID.df.pkl",
        ),
        (  # ts1 - units of time
            "datasc.df.pkl",
            {
                "time": "time",
                "signal": "signal",
                "species": {
                    "CO": {"l": 511.8, "r": 521.4},
                    "methane": {"l": 521.4, "r": 526.8},
                    "CO2": {"l": 529.2, "r": 538.8},
                    "ethylene": {"l": 541.8, "r": 550.2},
                    "ethane": {"l": 552.6, "r": 558.0},
                    "propylene": {"l": 595.2, "r": 602.0},
                    "propane": {"l": 602.0,"r": 606.0},
                },
                "output": "FID",
            },
            "FID.df.pkl",
        ),
        (  # ts2 - explicit units
            "datasc.df.pkl",
            {
                "time": "time",
                "signal": "signal",
                "species": {
                    "CO": {"l": "8.53 min", "r": "8.69 min"},
                    "methane": {"l": "8.69 min", "r": "8.78 min"},
                    "CO2": {"l": "8.82 min", "r": "8.98 min"},
                    "ethylene": {"l": "9.03 min", "r": "9.17 min"},
                    "ethane": {"l": "9.21 min", "r": "9.30 min"},
                    "propylene": {"l": "9.92 min", "r": "10.03 min"},
                    "propane": {"l": "10.03 min","r": "10.10 min"},
                },
                "output": "FID",
            },
            "FID.df.pkl",
        ),
    ],
)
def test_chromatography_integrate_trace(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    df = chromatography.integrate_trace(df, **spec)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)
