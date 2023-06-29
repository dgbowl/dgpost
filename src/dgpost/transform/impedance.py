"""
.. codeauthor::
    Ueli Sauter,
    Peter Kraus

Including functions relevant for Electrochemical Impedance Spectroscopy (EIS):
evaluation of an equivalent circuit as well as the fitting of the circuit to data
(:func:`~dgpost.transform.impedance.calc_circuit` and
:func:`~dgpost.transform.impedance.fit_circuit`), and an interpolation function
to find the :func:`~dgpost.transform.impedance.lowest_real_impedance` in the data.

.. rubric:: Functions

.. autosummary::

    calc_circuit
    fit_circuit
    lowest_real_impedance

.. note::
    The functions in this module expect the whole EIS trace as input - the
    :math:`\\text{Re}(Z)`, :math:`-\\text{Im}(Z)` and :math:`f` are expected to
    be :class:`pint.Quantity` containing an :class:`np.ndarray` (or similar
    :class:`list`-like object), which is then processed to a (set of) scalar
    values. This means that for processing time resolved data, the functions
    in this module have to be called on each timestep individually.

"""
import logging
from typing import Union
import numpy as np
import pint
import uncertainties as uc

from .circuit_utils.circuit_parser import parse_circuit, fit_routine
from dgpost.utils.helpers import separate_data, load_data

logger = logging.getLogger(__name__)


@load_data(
    ("real", "Ω", list),
    ("imag", "Ω", list),
    ("freq", "Hz", list),
)
def fit_circuit(
    real: pint.Quantity,
    imag: pint.Quantity,
    freq: pint.Quantity,
    circuit: str,
    initial_values: dict[str, float],
    fit_bounds: dict[str, tuple[float, float]] = None,
    fit_constants: list[str] = None,
    ignore_neg_res: bool = True,
    upper_freq: float = np.inf,
    lower_freq: float = 0,
    repeat: int = 1,
    output: str = "fit_circuit",
) -> dict[str, Union[int, str, pint.Quantity]]:
    """
    Fits an equivalent circuit to the frequency-resolved EIS data.

    For the fitting an equivalent circuit is needed, defined as a :class:`str`.
    The circuit may be composed of multiple circuit elements. To combine elements
    in a series a dash (``-``) is used. Elements in parallel are wrapped by
    ``p( , )``. An element is defined by an identifier (usually letters) followed
    by a digit. Already implemented elements are located in the
    :mod:`.circuit_utils.circuit_components` module:

    +------------------------+--------+------------+---------------+--------------+
    | Name                   | Symbol | Parameters | Bounds        | Units        |
    +========================+========+============+===============+==============+
    | Resistor               | ``R``  | ``R``      | (1e-6, 1e6)   | Ω            |
    +------------------------+--------+------------+---------------+--------------+
    | Capacitance            | ``C``  | ``C``      | (1e-20, 1)    | F            |
    +------------------------+--------+------------+---------------+--------------+
    | Constant Phase Element | ``CPE``| ``CPE_Q``  | (1e-20, 1)    | Ω⁻¹sᵃ        |
    |                        |        +------------+---------------+--------------+
    |                        |        | ``CPE_a``  | (0, 1)        |              |
    +------------------------+--------+------------+---------------+--------------+
    | Warburg element        | ``W``  | ``W``      | (0, 1e10)     | Ω⁻¹s¹ᐟ²      |
    +------------------------+--------+------------+---------------+--------------+
    | Warburg short element  | ``Ws`` | ``Ws_R``   | (0, 1e10)     | Ω            |
    |                        |        +------------+---------------+--------------+
    |                        |        | ``Ws_T``   | (1e-10, 1e10) | s            |
    +------------------------+--------+------------+---------------+--------------+
    | Warburg open element   | ``Wo`` | ``Wo_R``   | (0, 1e10)     | Ω            |
    |                        |        +------------+---------------+--------------+
    |                        |        | ``Wo_T``   | (1e-10, 1e10) | s            |
    +------------------------+--------+------------+---------------+--------------+

    Additionally an initial guess for the fitting parameters is needed. The initial
    guess is given as a :class:`dict` where each key is the parameter name and the
    corresponding value is the initial value for the circuit.

    The bounds of each parameter can be customized by the ``fit_bounds`` parameter.
    This parameter is a :class:`dict`, where each key is the parameter name and the
    value consists of a :class:`tuple` for the lower and upper bound (lb, ub).

    To hold a parameter constant, add the name of the parameter to a :class:`list`
    and pass it as ``fit_constants``

    Parameters
    ----------
    real
        A :class:`pint.Quantity` object containing the real part of the impedance data,
        :math:`\\text{Re}(Z)`. The unit of the provided gets converted to 'Ω'.

    imag
        A :class:`pint.Quantity` object containing the imaginary part of the impedance
        data, :math:`-\\text{Im}(Z)`. The unit of the provided gets converted to 'Ω'.

    freq
        A :class:`pint.Quantity` object containing the frequency :math:`f` of the
        impedance data. The unit of the provided data should gets converted to 'Hz'.

    circuit
        A :class:`str` description of the equivalent circuit.

    initial_values
        A :class:`dict` with the initial (guess) values.
        Structure: {"param name": value, ... }

    output
        A :class:`str` prefix

    fit_bounds
        Custom bounds for a parameter if default bounds are not wanted
        Structure: {"param name": (lower bound, upper bound), ...}
        Default is ''None''

    fit_constants
        list of parameters which should stay constant during fitting
        Structure: ["param name", ...]
        Default is ''None''

    ignore_neg_res
        ignores impedance values with a negative real part

    upper_freq:
        upper frequency bound to be considered for fitting

    lower_freq:
        lower frequency bound to be considered for fitting

    repeat
        how many times ``fit_routine`` gets called

    Returns
    -------
    (parameters, units)
        A tuple containing two dicts.
         - parameters, contains all the values of the parameters accessible by their names
         - units, contains all the units of the parameters accessible by their names
    """
    # normalise input units and get nominal values of the input data
    real_data = separate_data(real, "Ω")[0]
    imag_data = separate_data(imag, "Ω")[0]
    freq_data = separate_data(freq, "Hz")[0]

    # select appropriate data
    # select only frequency in the allowed range
    mask = np.logical_and(lower_freq < freq_data, freq_data < upper_freq)
    if ignore_neg_res:
        # ignore negative real
        mask = np.logical_and(mask, real_data > 0)

    frequency = freq_data[mask]
    z = real_data[mask] - 1j * imag_data[mask]

    # interpret fit circuit
    param_info, circ_calc = parse_circuit(circuit)

    if fit_bounds is None:
        fit_bounds = {}

    if fit_constants is None:
        fit_constants = []

    param_values = initial_values.copy()  # stores all the values of the parameters
    variable_names = []  # name of the parameters that are not fixed
    variable_guess = []  # guesses for the parameters that are not fixed
    variable_bounds = []  # bounds of the parameters that are not fixed

    for p in param_info:
        if p["name"] in initial_values:
            if p["name"] not in fit_constants:
                variable_bounds.append(fit_bounds.get(p["name"], p["bounds"]))
                variable_guess.append(initial_values.get(p["name"]))
                variable_names.append(p["name"])
        else:
            raise ValueError(f"No initial value given for {p['name']}")

    # calculate the weight of each datapoint
    def weight(error, value):
        """calculates the absolute value squared and divides the error by it"""
        square_value = value.real**2 + value.imag**2
        return np.true_divide(error, square_value)

    # calculate rmse
    def rmse(predicted, actual):
        """Calculates the root mean squared error between two vectors"""
        e = np.abs(np.subtract(actual, predicted))
        se = np.square(e)
        wse = weight(se, actual)
        mse = np.nansum(wse)
        return np.sqrt(mse)

    # prepare optimizing function:
    def opt_func(x: list[float]):
        params = dict(zip(variable_names, x))
        param_values.update(params)
        predict = circ_calc(param_values, frequency)
        err = rmse(predict, z)
        return err

    # fit
    opt_result = fit_routine(
        opt_func,
        variable_guess,
        variable_bounds,
        repeat=repeat,
    )

    # update values in ParameterList
    param_values.update(dict(zip(variable_names, opt_result.x)))

    # create output dictionaries
    retval = {f"{output}->circuit": circuit}

    # iterate over param_info, construct parameter name, and convert parameter
    # values to pint.Quantities
    for p in param_info:
        col_name = f"{output}->{p['name']}"
        retval[col_name] = pint.Quantity(param_values[p["name"]], p["unit"])

    return retval


@load_data(
    ("freq", "Hz", list),
)
def calc_circuit(
    freq: pint.Quantity,
    circuit: str,
    parameters: dict[str, float],
    output: str = "calc_circuit",
) -> tuple[dict[str, float], dict[str, str]]:
    """
    Calculates the complex impedance :math:`\\text{Re}(Z)` and :math:`-\\text{Im}(Z)`
    of the prescribed equivalent circuit as a function of frequency :math:`f`.

    Parameters
    ----------
    freq
        A :class:`pint.Quantity` containing the frequencies :math:`f` at which the
        equivalent circuit is to be evaluated. The provided data should be in "Hz".

    circuit
        A :class:`str` description of the equivalent circuit. For more details see
        :func:`fit_circuit`.

    parameters
        A :class:`dict` containing the values defining the equivalent circuit.
        Structure: {"param name": value, ... }

    output
        A :class:`str` prefix for the ``Re(Z)`` and ``-Im(Z)`` values calculated
        in this function. Defaults to ``"calc_circuit"``.


    Returns
    -------
    retvals: dict[str, pint.Quantity]
        A dictionary containing the :class:`pint.Quantity` arrays with the
        output-prefixed :math:`\\text{Re}(Z)` and :math:`-\\text{Im}(Z)` as keys.
    """
    # separate the freq data into values, errors and normalize the unit
    freq_data = separate_data(freq, "Hz")[0]

    # parse the circuit
    param_info, circ_calc = parse_circuit(circuit)

    # check if every parameter has a value
    for p in param_info:
        if p["name"] not in parameters:
            raise ValueError(f"No initial value given for {p['name']}")

    # calculate the impedance
    impedance = circ_calc(parameters, freq_data)

    # generate the output
    real_name = f"{output}->Re(Z)"
    imag_name = f"{output}->-Im(Z)"

    retval = {
        real_name: pint.Quantity(impedance.real, "Ω"),
        imag_name: pint.Quantity(-impedance.imag, "Ω"),
    }

    return retval


@load_data(
    ("real", "Ω", list),
    ("imag", "Ω", list),
)
def lowest_real_impedance(
    real: pint.Quantity,
    imag: pint.Quantity,
    threshold: float = 0.0,
    output: str = "min Re(Z)",
) -> dict[str, Union[int, str, pint.Quantity]]:
    """
    A function that finds and interpolates the lowest :math:`\\text{Re}(Z)` value
    at which the complex impedance :math:`Z = \\text{Re}(Z) - j \\text{Im}(Z)` is a
    real number (i.e. :math:`\\text{Im}(Z) \\approx 0`). If the impedance does not
    cross the real-zero axis, the :math:`\\text{Re}(Z)` at which the
    :math:`\\text{abs}(\\text{Im}(Z))` is the smallest is returned.

    Parameters
    ----------
    real
        A :class:`pint.Quantity` object containing the real part of the impedance data,
        :math:`\\text{Re}(Z)`. The units of ``real`` and ``imag`` are assumed to match.

    imag
        A :class:`pint.Quantity` object containing the imaginary part of the impedance
        data, :math:`-\\text{Im}(Z)`. The units of ``real`` and ``imag`` are assumed to
        match.

    output
        A :class:`str` name for the output column, defaults to ``"min Re(Z)"``.

    Returns
    -------
    retvals: dict[str, pint.Quantity]
        A dictionary containing the :class:`pint.Quantity` values of the real impedances
        with the output as keys.
    """

    s = np.argsort(real)
    real = real[s]
    imag = imag[s]
    if imag[0] > 0:
        izeros = np.flatnonzero(imag < threshold)
    else:
        izeros = np.flatnonzero(imag > threshold)
    if izeros.size == 0:
        logger.warning(
            "No real impedance found. Returning real part of impedance "
            "with the smallest complex component."
        )
        iz = abs(imag).argmin()
        z, u = real[iz].m, real[iz].u
    else:
        iz = izeros[0]
        if iz == real.size:
            im = imag[iz - 1 :]
            re = real[iz - 1 :]
        else:
            im = imag[iz - 1 : iz + 1]
            re = real[iz - 1 : iz + 1]

        imv, ime, imu = separate_data(im)
        rev, ree, reu = separate_data(re)

        zv = np.interp(0, imv, rev)
        ze = np.interp(0, ime, ree)
        z = uc.ufloat(zv, ze)
        u = reu

    return {output: pint.Quantity(z, u)}
