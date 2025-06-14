import pytest
import numpy as np
import pint

from dgpost.transform import complex

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
            [pint.Quantity(np.ones(3)*np.sqrt(2)), np.ones(3)*pint.Quantity("45 deg")]
        ),
        (
            np.array([3, 3, -3, -3, 4]),
            np.array([4, -4, 4, -4, 3]),
            [
                pint.Quantity([5, 5, 5, 5, 5], "dimensionless"),
                pint.Quantity([36.8698, 143.1301, -36.8698, -143.1301, 53.1301], "deg"),
            ]
        ),
    ]
)
def test_complex_roundtrip(x, y, polar):
    ret = complex.to_polar(x, y)
    print(f"{ret=}")
    assert np.allclose(ret["mag"], polar[0], equal_nan=True)
    assert np.allclose(ret["arg"], polar[1], equal_nan=True)

    bck = complex.to_rectangular(polar[0], polar[1])
    print(f"{bck=}")
    assert np.allclose(x, bck["x"], equal_nan=True, atol=1e-6)
    assert np.allclose(y, bck["y"], equal_nan=True, atol=1e-6)
