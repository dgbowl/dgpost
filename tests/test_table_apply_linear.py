import pytest
import numpy as np
import pint
from uncertainties.unumpy import uarray, nominal_values, std_devs
from uncertainties import ufloat
from dgpost.transform import table


@pytest.mark.parametrize(
    "x, slope, intercept, output, y",
    [
        (
            1,
            1,
            0,
            "test",
            1,
        ),
        (
            [2, 4, 6, 8],
            0.5,
            0.1,
            "test",
            [1.1, 2.1, 3.1, 4.1],
        ),
        (
            pint.Quantity([10, 12, 10], "second"),
            pint.Quantity("0.5 meter/second"),
            pint.Quantity("0.1 meter"),
            "test",
            pint.Quantity([5.1, 6.1, 5.1], "meter"),
        ),
        (
            pint.Quantity([10, 12, 10], "second"),
            pint.Quantity(ufloat(0.5, 0.0), "meter/second"),
            pint.Quantity(ufloat(0.0, 0.5), "meter"),
            "output",
            pint.Quantity(uarray([5.0, 6.0, 5.0], [0.5, 0.5, 0.5]), "meter"),
        ),
        (
            pint.Quantity([10, 12, 10], "second"),
            "0.5 meter/second",
            "0.0(5) meter",
            "output",
            pint.Quantity(uarray([5.0, 6.0, 5.0], [0.5, 0.5, 0.5]), "meter"),
        ),
        (
            pint.Quantity([10, 12, 10], "second"),
            "1.00+/-0.01 meter/second",
            0.0,
            "output",
            pint.Quantity(uarray([10.0, 12.0, 10.0], [0.1, 0.12, 0.1]), "meter"),
        ),
        (
            pint.Quantity([10, np.nan, np.inf, 0.0], "second"),
            "1.50 meter/second",
            "0.0 meter",
            "output",
            pint.Quantity([15.0, np.nan, np.inf, np.nan], "meter"),
        ),
        (
            pint.Quantity([10, np.nan, np.inf, 0.0], "second"),
            "1.50 meter/second",
            "0.0(5) meter",
            "output",
            pint.Quantity(uarray([15.0, np.nan, np.inf, np.nan], [0.5] * 4), "meter"),
        ),
    ],
)
def test_table_apply_linear(x, slope, intercept, output, y):
    ret = table.apply_linear(column=x, slope=slope, intercept=intercept, output=output)
    print(f"{ret=}")
    print(f"{y=}")
    for func in {nominal_values, std_devs}:
        assert np.allclose(func(ret[output]), func(y), equal_nan=True)


def test_table_apply_linear_namespace():
    ns = {"a": [10, 11, 12], "b": [5, 6, 7]}
    ret = table.apply_linear(namespace=ns, slope=2.0, intercept=1.0, output="ns")
    x = {"ns->a": [21, 23, 25], "ns->b": [11, 13, 15]}
    for k, v in ret.items():
        assert np.allclose(ret[k], x[k])


def test_table_apply_linear_minmax():
    ret = table.apply_linear(
        column=pint.Quantity([0.0, 0.1, 0.5, 1.0]),
        slope=2.0,
        intercept=-0.5,
        minimum=0.0,
        nonzero_only=True,
    )
    assert np.allclose(
        ret["output"],
        pint.Quantity([np.nan, 0, 0.5, 1.5]),
        atol=0,
        rtol=0,
        equal_nan=True,
    )

    ret = table.apply_linear(
        column=pint.Quantity([0.0, 0.1, 0.5, 1.0], "meter"),
        slope=2.0,
        intercept="0.5 centimeter",
        maximum="2 meter",
        nonzero_only=False,
    )
    assert np.allclose(
        ret["output"],
        pint.Quantity([0.005, 0.205, 1.005, 2.0], "meter"),
    )

    ret = table.apply_linear(
        column=pint.Quantity(uarray([0.1, 0.5, 1.0], [0.1, 0.1, 0.1]), "meter"),
        slope=2.0,
        intercept="0.5(5) centimeter",
        maximum="2 meter",
    )
    print(f"{ret=}")
    assert np.allclose(nominal_values(ret["output"]), [0.205, 1.005, 2.0])
    assert np.allclose(std_devs(ret["output"]), [0.20006, 0.20006, 0.0], atol=1e-5)


@pytest.mark.parametrize(
    "y, slope, intercept, output, x",
    [
        (
            1,
            1,
            0,
            "test",
            1,
        ),
        (
            [2, 4, 6, 8],
            0.5,
            0.1,
            "test",
            [3.8, 7.8, 11.8, 15.8],
        ),
        (
            pint.Quantity([10.1, 12.1, 10.1], "meter"),
            "0.5 meter/second",
            "0.1 meter",
            "test",
            pint.Quantity([20, 24, 20], "second"),
        ),
    ],
)
def test_table_apply_inverse(y, slope, intercept, output, x):
    ret = table.apply_inverse(column=y, slope=slope, intercept=intercept, output=output)
    print(f"{ret=}")
    print(f"{x=}")
    for func in {nominal_values, std_devs}:
        assert np.allclose(func(ret[output]), func(x))


def test_table_apply_inverse_namespace():
    ns = {"a": np.array([10, 11, 12]), "b": 6}
    ret = table.apply_inverse(namespace=ns, slope=2.0, intercept=1.0, output="ns")
    print(f"{ret=}")
    x = {"ns->a": [4.5, 5.0, 5.5], "ns->b": 2.5}
    for k, v in ret.items():
        assert np.allclose(ret[k], x[k])


def test_table_apply_inverse_minmax():
    ret = table.apply_inverse(
        column=pint.Quantity([0.1, 0.5, 1.0]),
        slope=0.5,
        intercept=0.5,
        minimum=0.0,
    )
    assert np.allclose(ret["output"], pint.Quantity([0, 0, 1]), atol=0, rtol=0)

    ret = table.apply_inverse(
        column=pint.Quantity([0.1, 0.5, 1.0], "meter"),
        slope=0.1,
        intercept="0.5 centimeter",
        maximum="2 meter",
    )
    assert np.allclose(ret["output"], pint.Quantity([0.95, 2.0, 2.0], "meter"))

    ret = table.apply_inverse(
        column=pint.Quantity(uarray([0.1, 0.5, 1.0], [0.1, 0.1, 0.1]), "meter"),
        slope=0.1,
        intercept="0.5(5) centimeter",
        maximum="2 meter",
    )
    print(f"{ret=}")
    assert np.allclose(nominal_values(ret["output"]), [0.95, 2.0, 2.0])
    assert np.allclose(std_devs(ret["output"]), [1.00124, 0.0, 0.0], atol=1e-5)
