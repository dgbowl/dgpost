"""
A set of functions used to create the test data present in ``rawData``. The dataframes (*.pkl)
contain "synthetic" data created using the ``parse_circuit`` function. The datagrams (*.dg.json)
contain "measured" data from .mpr files, where the properties of a dummy cell were recorded.

"""
import os


import numpy as np
import pandas as pd

from dgpost.transform.circuit_utils.circuit_parser import parse_circuit


def setup(params=None):
    if params is None:
        params = {
            "R0": 100,
            "R1": 250,
            "C1": 1e-8,
            "R2": 150,
            "C2": 1e-6,
        }
    circuit = "R0-p(R1,C1)-p(R2,C2)"

    info, calc = parse_circuit(circuit)

    freq = np.logspace(-3, 9, 120)

    impedance = calc(params, freq)

    real = impedance.real

    imag = impedance.imag

    return {"freq": [freq], "Re(Z)": [real], "-Im(Z)": [-imag]}


def single_df():
    cols = setup()
    df = pd.DataFrame.from_dict(cols)
    df.attrs["units"] = {"freq": "Hz", "Re(Z)": "Ω", "-Im(Z)": "Ω"}
    df.to_pickle("test.single.Data.pkl")


def multiple_df():
    cols = setup()
    df = pd.DataFrame.from_dict(cols)
    df = df.append(
        setup(params={"R0": 300, "R1": 550, "C1": 1e-9, "R2": 250, "C2": 1e-5,}),
        ignore_index=True,
    )
    df.attrs["units"] = {"freq": "Hz", "Re(Z)": "Ω", "-Im(Z)": "Ω"}
    df.to_pickle("test.multiple.Data.pkl")


def single_dg():
    os.system(r"yadg process rawData\create_single_dg.json peis.single.data.dg.json")


def multiple_dg():
    os.system(
        r"yadg process rawData\create_multiple_dg.json peis.multiple.data.dg.json"
    )


if __name__ == "__main__":
    single_df()
    single_dg()
    multiple_df()
    multiple_dg()
