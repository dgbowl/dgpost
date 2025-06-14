import pytest
import numpy as np
import pandas as pd
import pint
import os
from dgpost.transform import complex

from .utils import compare_dfs


@pytest.mark.parametrize(
    "x, y, polar",
    [
        (
            1,
            1,
            [pint.Quantity(np.sqrt(2)), pint.Quantity("45 degree")],
        ),
        (
            [1, 1, 1],
            [1, 1, 1],
            [
                pint.Quantity(np.ones(3) * np.sqrt(2)),
                np.ones(3) * pint.Quantity("45 deg"),
            ],
        ),
        (
            np.array([3, 3, -3, -3, 4]),
            np.array([4, -4, 4, -4, 3]),
            [
                pint.Quantity([5, 5, 5, 5, 5], "dimensionless"),
                pint.Quantity([53.1301, -53.1301, 126.8699, -126.8699, 36.8698], "deg"),
            ],
        ),
    ],
)
def test_complex_roundtrip(x, y, polar):
    ret = complex.to_polar(x, y)
    print(f"{ret=}")
    print(polar)
    assert np.allclose(ret["mag"], polar[0])
    assert np.allclose(ret["arg"], polar[1])

    bck = complex.to_rectangular(polar[0], polar[1])
    print(f"{bck=}")
    assert np.allclose(bck["x"], x, atol=1e-6)
    assert np.allclose(bck["y"], y, atol=1e-6)


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - qftrace 2 datapoints
            "qftrace.2.pkl",
            {"x": "S11->Re(Γ)", "y": "S11->Im(Γ)", "output": "S11"},
            "ref.qftrace.2.pkl",
        )
    ],
)
def test_complex_to_polar_df(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    df = complex.to_polar(df, **spec)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - qftrace 2 datapoints
            "ma.pkl",
            {"mag": "mag", "arg": "ang", "output": None},
            "ref.ma.pkl",
        )
    ],
)
def test_complex_to_rectangular_df(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    df = complex.to_rectangular(df, **spec)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)
