import os
import pytest
import pandas as pd
import pint
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
                        "l": pint.Quantity(511.8, "s"),
                        "r": pint.Quantity(521.4, "s"),
                    },
                    "methane": {
                        "l": pint.Quantity(521.4, "s"),
                        "r": pint.Quantity(526.8, "s"),
                    },
                    "CO2": {
                        "l": pint.Quantity(529.2, "s"),
                        "r": pint.Quantity(538.8, "s"),
                    },
                    "ethylene": {
                        "l": pint.Quantity(541.8, "s"),
                        "r": pint.Quantity(550.2, "s"),
                    },
                    "ethane": {
                        "l": pint.Quantity(552.6, "s"),
                        "r": pint.Quantity(558.0, "s"),
                    },
                    "propylene": {
                        "l": pint.Quantity(595.2, "s"),
                        "r": pint.Quantity(602.0, "s"),
                    },
                    "propane": {
                        "l": pint.Quantity(602.0, "s"),
                        "r": pint.Quantity(606.0, "s"),
                    },
                    "butane": {
                        "l": pint.Quantity(690.0, "s"),
                        "r": pint.Quantity(696.0, "s"),
                    },
                    "acetic": {
                        "l": pint.Quantity(249.6, "s"),
                        "r": pint.Quantity(260.4, "s"),
                    },
                    "acrylic": {
                        "l": pint.Quantity(307.2, "s"),
                        "r": pint.Quantity(318.0, "s"),
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
                    "propane": {"l": 602.0, "r": 606.0},
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
                    "propane": {"l": "10.03 min", "r": "10.10 min"},
                },
                "output": "FID",
            },
            "FID.df.pkl",
        ),
        (  # ts3 - LC data
            "agilent.df.pkl",
            {
                "time": "LC->t",
                "signal": "LC->y",
                "species": {
                    "formic acid": {"l": "14.5 min", "r": "15.5 min"},
                    "acetic acid": {"l": "15.5 min", "r": "16.5 min"},
                    "ethanol": {"l": "21.2 min", "r": "22.0 min"},
                    "allyl alcohol": {"l": "22.0 min", "r": "22.8 min"},
                    "1-propanol": {"l": "27.7 min", "r": "28.7 min"},
                },
                "output": "LC",
            },
            "LC.df.pkl",
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


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - explicit units
            "FID.df.pkl",
            {
                "areas": "FID->area",
                "calibration": {
                    "CO": {"function": "inverse", "m": "1873.56 pA·s/%"},
                    "methane": {"function": "inverse", "m": "1795.41 pA·s/%"},
                    "CO2": {"function": "inverse", "m": "1841.64 pA·s/%"},
                    "ethylene": {"function": "inverse", "m": "3565.07 pA·s/%"},
                    "ethane": {"function": "inverse", "m": "3570.01 pA·s/%"},
                    "propylene": {"function": "inverse", "m": "5306.26 pA·s/%"},
                    "propane": {"function": "inverse", "m": "5326.11 pA·s/%"},
                    "butane": {"function": "inverse", "m": "7121.53 pA·s/%"},
                },
                "output": "x",
            },
            "ts0.df.pkl",
        ),
        (  # ts1 - LC data
            "LC.df.pkl",
            {
                "areas": "LC->area",
                "calibration": {
                    "formic acid": {
                        "function": "inverse",
                        "m": "8314 (nRIU·s)/(mmol/l)",
                    },
                    "acetic acid": {
                        "function": "inverse",
                        "m": "15490 (nRIU·s)/(mmol/l)",
                    },
                    "ethanol": {"function": "inverse", "m": "10787 (nRIU·s)/(mmol/l)"},
                    "allyl alcohol": {
                        "function": "inverse",
                        "m": "25387 (nRIU·s)/(mmol/l)",
                    },
                    "1-propanol": {
                        "function": "inverse",
                        "m": "20628 (nRIU·s)/(mmol/l)",
                    },
                },
                "output": "c",
            },
            "ts1.df.pkl",
        ),
    ],
)
def test_chromatography_apply_calibration(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    df = chromatography.apply_calibration(df, **spec)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)
