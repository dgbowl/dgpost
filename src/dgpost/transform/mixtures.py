"""
.. codeauthor::
    Peter Kraus

Includes functions to convert namespaces containing mixtures of chemicals between
various representations, such as mole fractions etc.

.. rubric:: Functions

.. autosummary::

    flows_to_fractions
    fractions_to_flows

"""

import pint
import numpy as np

from dgpost.utils.helpers import load_data, fill_nans

ureg = pint.get_application_registry()


@load_data(
    ("total", "m³/s"),
    ("vdot", "m³/s", dict),
)
def flows_to_fractions(
    total: pint.Quantity,
    vdot: dict[str, pint.Quantity] = None,
    output: str = "x",
    _inp: dict = {},
) -> dict[str, pint.Quantity]:
    """
    Calculates the volume fractions of components in the provided namespace ``vdot``,
    given the total flow in ``total``.

    Parameters
    ----------
    total
        The total flow, by default in m³/s. Negative or zero values are ignored.

    vdot
        The dictionary containing flows of all species/components. By default in m³/s.

    output
        Prefix of the output namespace. Defaults to "x" for mole fraction.

    """
    ret = {}
    temp = np.where(total > 0, total, np.nan)
    for k, v in vdot.items():
        if _inp["total"] == f"{_inp['vdot']}->{k}":
            continue
        ret[f"{output}->{k}"] = v / temp
    return ret


@load_data(
    ("total", "m³/s"),
    ("x", None, dict),
)
def fractions_to_flows(
    total: pint.Quantity,
    x: dict[str, pint.Quantity] = None,
    fillnan: bool = True,
    output: str = "x",
    _inp: dict = {},
) -> dict[str, pint.Quantity]:
    """
    Calculates the volume fractions of components in the provided namespace ``vdot``,
    given the total flow in ``total``.

    Parameters
    ----------
    total
        The total flow, by default in m³/s. Negative or zero values are ignored.

    vdot
        The dictionary containing flows of all species/components. By default in m³/s.

    output
        Prefix of the output namespace. Defaults to "x" for mole fraction.

    """
    ret = {}
    temp = np.where(total > 0, total, np.nan)
    for k, v in x.items():
        if fillnan:
            v = fill_nans(v, fillmag=0.0)
        ret[f"{output}->{k}"] = v * temp
    return ret
