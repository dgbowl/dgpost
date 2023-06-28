import json
import os

import numpy as np
import pandas as pd
from uncertainties import unumpy as unp
import pytest
from dgpost.transform import impedance
from dgpost.utils import extract, transform
import pint


@pytest.mark.parametrize(
    "filepath, fit_info, expected",
    [
        (
            "test.trans.data.pkl",
            [
                {
                    "real": "Re(Z)",
                    "imag": "-Im(Z)",
                    "freq": "freq",
                    "circuit": "R0-p(R1,C1)-p(R2,C2)",
                    "initial_values": {
                        "R0": 90,
                        "R1": 240,
                        "C1": 3e-8,
                        "R2": 140,
                        "C2": 3e-6,
                    },
                },
            ],
            [
                {
                    "circuit": "R0-p(R1,C1)-p(R2,C2)",
                    "R0": 100,
                    "R1": 250,
                    "C1": 1e-8,
                    "R2": 150,
                    "C2": 1e-6,
                }
            ],
        ),
        (
            "test.multi.data.pkl",
            [
                {
                    "real": "Re(Z)",
                    "imag": "-Im(Z)",
                    "freq": "freq",
                    "circuit": "R0-p(R1,C1)-p(R2,C2)",
                    "initial_values": {
                        "R0": 90,
                        "R1": 240,
                        "C1": 3e-8,
                        "R2": 140,
                        "C2": 3e-6,
                    },
                },
            ],
            [
                {
                    "circuit": "R0-p(R1,C1)-p(R2,C2)",
                    "R0": 100,
                    "R1": 250,
                    "C1": 1e-8,
                    "R2": 150,
                    "C2": 1e-6,
                },
                {
                    "circuit": "R0-p(R1,C1)-p(R2,C2)",
                    "R0": 300,
                    "R1": 550,
                    "C1": 1e-9,
                    "R2": 250,
                    "C2": 1e-5,
                },
            ],
        ),
        (
            "extracted.single.pkl",
            [
                {
                    "real": "Re(Z)",
                    "imag": "-Im(Z)",
                    "freq": "freq",
                    "circuit": "R0-p(R1,C1)-p(R2,C2)",
                    "initial_values": {
                        "R0": 500,
                        "R1": 800,
                        "R2": 300,
                        "C1": 1e-9,
                        "C2": 1e-5,
                    },
                },
            ],
            [
                {
                    "circuit": "R0-p(R1,C1)-p(R2,C2)",
                    "R0": 475.2433212762373,
                    "R1": 1017.9841560981195,
                    "R2": 3560.8270276185403,
                    "C1": 8.217441694839528e-09,
                    "C2": 2.3013607605373074e-06,
                }
            ],
        ),
        (
            "extracted.multiple.pkl",
            [
                {
                    "real": "Re(Z)",
                    "imag": "-Im(Z)",
                    "freq": "freq",
                    "circuit": "R0-p(R1,C1)-p(R2,C2)",
                    "initial_values": {
                        "R0": 500,
                        "R1": 800,
                        "R2": 300,
                        "C1": 1e-9,
                        "C2": 1e-5,
                    },
                }
            ],
            [
                {
                    "circuit": "R0-p(R1,C1)-p(R2,C2)",
                    "R0": 475.21080042727726,
                    "R1": 1018.377668250544,
                    "R2": 3561.2257211299725,
                    "C1": 8.152810550867264e-09,
                    "C2": 2.30438916633477e-06,
                },
                {
                    "circuit": "R0-p(R1,C1)-p(R2,C2)",
                    "R0": 475.2953789139291,
                    "R1": 1018.442597093697,
                    "R2": 3560.7868174294067,
                    "C1": 8.151962523603272e-09,
                    "C2": 2.3037006497998636e-06,
                },
                {
                    "circuit": "R0-p(R1,C1)-p(R2,C2)",
                    "R0": 475.1262422077364,
                    "R1": 1019.6598850783428,
                    "R2": 3559.517708873706,
                    "C1": 8.148917576672245e-09,
                    "C2": 2.3053411072402693e-06,
                },
            ],
        ),
    ],
)
def test_impedance_fit_circuit_df(filepath, fit_info, expected, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(filepath)
    df = transform(df, "impedance.fit_circuit", using=fit_info)
    for index, expect in enumerate(expected):
        for col in df["fit_circuit"].columns:
            value = df["fit_circuit"][col].iloc[index]
            assert col in expect
            assert value == pytest.approx(expect[col])


def test_impedance_fit_circuit_direct(datadir):
    os.chdir(datadir)
    df = pd.read_pickle("test.plain.data.pkl")
    real = df["Re(Z)"]
    imag = df["-Im(Z)"]
    freq = df["freq"]
    fit_info = {
        "circuit": "R0-p(R1,C1)-p(R2,C2)",
        "initial_values": {
            "R0": 90,
            "R1": 240,
            "C1": 3e-8,
            "R2": 140,
            "C2": 3e-6,
        },
    }
    retvals = impedance.fit_circuit(real, imag, freq, **fit_info)
    expected = {
        "circuit": "R0-p(R1,C1)-p(R2,C2)",
        "R0": pint.Quantity(100.0, "ohm"),
        "R1": pint.Quantity(250.0, "ohm"),
        "C1": pint.Quantity(1e-8, "farad"),
        "R2": pint.Quantity(150.0, "ohm"),
        "C2": pint.Quantity(1e-6, "farad"),
    }
    for key, val in retvals.items():
        ref = expected.get(key.split(">")[-1])
        assert val == ref or val.m == pytest.approx(ref)


def test_impedance_calc_circuit(datadir):
    os.chdir(datadir)
    calc_info = [
        {
            "circuit": "R0-p(R1,C1)-p(R2,C2)",
            "parameters": {
                "R0": 100,
                "R1": 250,
                "C1": 1e-8,
                "R2": 150,
                "C2": 1e-6,
            },
            "output": "test",
            "freq": "freq",
        }
    ]
    df = pd.DataFrame.from_dict({"freq": [np.logspace(-3, 9, 120)]})
    df.attrs["units"] = {"freq": "Hz"}
    df = transform(df, "impedance.calc_circuit", using=calc_info)
    ref = pd.read_pickle("test.trans.data.pkl")
    for col in df["test"].columns:
        pd.testing.assert_series_equal(ref[col], df["test"][col])
        assert ref.attrs["units"][col] == df.attrs["units"][f"test"][col]


@pytest.mark.parametrize(
    "filepath, inp_extr, inp_using, expected",
    [
        (
            "peis1.dg.json",
            {
                "at": {"index": 0},
                "columns": [
                    {"key": "raw->traces->PEIS->Re(Z)", "as": "Re(Z)"},
                    {"key": "raw->traces->PEIS->-Im(Z)", "as": "-Im(Z)"},
                ],
            },
            [{"real": "Re(Z)", "imag": "-Im(Z)"}],
            [
                14.800329,
                11.044216,
            ],
        ),
        (
            "peis2.dg.json",
            {
                "at": {"index": 0},
                "columns": [
                    {"key": "raw->traces->PEIS->Re(Z)", "as": "real"},
                    {"key": "raw->traces->PEIS->-Im(Z)", "as": "imag"},
                ],
            },
            [{"real": "real", "imag": "imag"}],
            [
                8.513345,
                11.355723,
                9.173434,
                10.407892,
                12.295147,
                8.395753,
                8.789996,
                9.496541,
                10.546235,
                12.573461,
                8.438693,
                8.911721,
                9.65812,
            ],
        ),
    ],
)
def test_impedance_lowest_real(filepath, inp_extr, inp_using, expected, datadir):
    os.chdir(datadir)
    with open(filepath, "r") as infile:
        dg = json.load(infile)
    df = extract(dg, inp_extr)
    df = transform(df, "impedance.lowest_real_impedance", using=inp_using)
    assert np.allclose(expected, unp.nominal_values(df["min Re(Z)"].squeeze()))
