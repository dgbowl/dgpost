"""
.. codeauthor::
    Peter Kraus

Provides convenience functions for converting complex numbers between rectangular and
polar forms.

.. rubric:: Functions

.. autosummary::

    to_rectangular
    to_polar


"""

import pint
import numpy as np
from uncertainties import unumpy as unp
from dgpost.utils.helpers import load_data


@load_data(
    ("mag", None, list),
    ("arg", "radians", list),
)
def to_rectangular(
    mag: pint.Quantity,
    arg: pint.Quantity,
    output: str = None,
) -> pint.Quantity:
    """
    Convert the provided complex number in polar form :math:`(r, θ)` to rectangular
    (or Cartesian) form :math:`(x, y)`.

    Parameters
    ----------
    mag
        The magnitude :math:`r`.

    arg
        The argument (or angle) :math:`θ`. By default in radians.

    output
        Name of the output namespace. Defaults to ``None``, which means ``x`` and ``y``
        will be returned.

    Returns
    -------
    dict(output, x) : dict[str, pint.Quantity]
        Returns the Cartesian x-coordinate.

    dict(output, y) : dict[str, pint.Quantity]
        Returns the Cartesian y-coordinate.

    """
    arg_rad = arg.to("radians")
    y = mag * unp.sin(arg_rad)
    x = mag * unp.cos(arg_rad)
    pretag = "" if output is None else f"{output}->"
    return {f"{pretag}x": x, f"{pretag}y": y}


@load_data(
    ("x", None, list),
    ("y", None, list),
)
def to_polar(
    x: pint.Quantity,
    y: pint.Quantity,
    output: str = None,
) -> pint.Quantity:
    """
    Convert the provided complex number in rectangular form :math:`(x, y)` to polar
    form :math:`(r, θ)`.

    Returns

    Parameters
    ----------
    x
        The Cartesian x-coordinate of the complex number.

    y
        The Cartesian y-coordinate of the complex number.

    output
        Name of the output namespace. Defaults to ``None``, which means ``mag`` and
        ``arg`` will be returned.

    Returns
    -------
    dict(output, mag) : dict[str, pint.Quantity]
        Returns the magnitude (r) of the complex number.

    dict(output, arg) : dict[str, pint.Quantity]
        Returns the argument (θ) of the complex number, in radians.

    """
    print(f"{x=}")
    x = np.asarray(x)
    y = np.asarray(y)
    print(f"{x=}")
    mag = pint.Quantity(unp.sqrt(x**2 + y**2), "dimensionless")
    arg = pint.Quantity(unp.arctan2(y, x), "radians")
    pretag = "" if output is None else f"{output}->"
    return {f"{pretag}mag": mag, f"{pretag}arg": arg}
