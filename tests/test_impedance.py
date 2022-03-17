import json
import os

import numpy as np
import pandas as pd
import pytest
from dgpost.transform import impedance
from dgpost.utils import extract, transform

from tests.utils import datadir


@pytest.mark.parametrize(
    "filepath, fit_info, expected",
    [
        (
            "test.single.Data.pkl",
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
            "test.multiple.Data.pkl",
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
    ],
)
def test_pkl_fit_circuit(filepath, fit_info, expected, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(filepath)

    transform(df, "impedance.fit_circuit", using=fit_info)

    cols = [col for col in df if col.startswith("fit")]
    for index, expect in enumerate(expected):
        assert len(cols) == len(expect)
        for col in cols:
            value = df[col].iloc[index]
            name = col.split(">")[-1]
            assert name in expect
            assert value == pytest.approx(expect[name])


@pytest.mark.parametrize(
    "data_info, fit_info, expected",
    [
        (
            {
                "filepath": "peis.single.data.dg.json",
                "spec": {
                    "at": {"index": 0},
                    "direct": [
                        {"key": "raw->traces->PEIS->Re(Z)", "as": "Re(Z)"},
                        {"key": "raw->traces->PEIS->-Im(Z)", "as": "-Im(Z)"},
                        {"key": "raw->traces->PEIS->freq", "as": "freq"},
                    ],
                },
            },
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
            {
                "filepath": "peis.multiple.data.dg.json",
                "spec": {
                    "at": {"index": 0},
                    "direct": [
                        {"key": "raw->traces->PEIS->Re(Z)", "as": "Re(Z)"},
                        {"key": "raw->traces->PEIS->-Im(Z)", "as": "-Im(Z)"},
                        {"key": "raw->traces->PEIS->freq", "as": "freq"},
                    ],
                },
            },
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
def test_dg_fit_circuit(data_info, fit_info, expected, datadir):
    os.chdir(datadir)
    with open(data_info["filepath"], "r") as infile:
        dg = json.load(infile)
    df = extract(dg, data_info["spec"])

    transform(df, "impedance.fit_circuit", using=fit_info)

    cols = [col for col in df if col.startswith("fit")]
    for index, expect in enumerate(expected):
        assert len(cols) == len(expect)
        for col in cols:
            value = df[col].iloc[index]
            name = col.split(">")[-1]
            assert name in expect
            assert value == pytest.approx(expect[name])


def test_direct_fit_circuit(datadir):
    os.chdir(datadir)
    df = pd.read_pickle("test.single.Data.pkl")

    real = df["Re(Z)"][0]
    imag = df["-Im(Z)"][0]
    freq = df["freq"][0]

    fit_info = {
        "circuit": "R0-p(R1,C1)-p(R2,C2)",
        "initial_values": {"R0": 90, "R1": 240, "C1": 3e-8, "R2": 140, "C2": 3e-6,},
    }

    parameters, units = impedance.fit_circuit(real, imag, freq, **fit_info)

    expected = {
        "circuit": "R0-p(R1,C1)-p(R2,C2)",
        "R0": 100,
        "R1": 250,
        "C1": 1e-8,
        "R2": 150,
        "C2": 1e-6,
    }

    for key in parameters:
        ret = parameters.get(key)
        ref = expected.get(key.split(">")[-1])
        assert ret == pytest.approx(ref)


def test_calc_circuit(datadir):
    os.chdir(datadir)
    calc_info = [
        {
            "circuit": "R0-p(R1,C1)-p(R2,C2)",
            "parameters": {"R0": 100, "R1": 250, "C1": 1e-8, "R2": 150, "C2": 1e-6,},
            "output": "test",
            "freq": "freq",
        }
    ]
    df = pd.DataFrame.from_dict({"freq": [np.logspace(-3, 9, 120)]})
    df.attrs["units"] = {"freq": "Hz"}

    transform(df, "impedance.calc_circuit", using=calc_info)

    ref = pd.read_pickle("test.single.Data.pkl")

    cols = [col for col in df if col.startswith("test")]
    for col in cols:
        name = col.split(">")[-1]
        np.testing.assert_array_equal(df[col].iloc[0], ref[name].iloc[0])
        assert df.attrs["units"][col] == ref.attrs["units"][name]
