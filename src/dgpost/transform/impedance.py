import logging
import warnings
from typing import Callable, Union

import numpy as np
import pandas as pd
import pint
import uncertainties.unumpy as unp
from uncertainties import ufloat
from scipy.optimize import least_squares, minimize

from .circuit_utils.circuit_parser import parse_circuit
from .helpers import separate_data, load_data

logger = logging.getLogger(__name__)


def fit_routine(
    opt_func: Callable[[list], float],
    fit_guess: list[float],
    bounds: list[tuple],
    repeat: int = 1,
):
    """
    Fitting routine which uses scipy least_squares and minimize.

    Least_squares is a good fitting method but will get stuck in local minima.
    For this reason, the Nelder-Mead-Simplex algorithm is used to get out of these local minima.
    The fitting routine is inspired by Relaxis 3 fitting procedure.
    More information about it can be found on page 188 of revision 1.25 of Relaxis User Manual.
    https://www.rhd-instruments.de/download/manuals/relaxis_manual.pdf

    Open issue is estimate the errors of the parameters. For further information look:
    - https://github.com/andsor/notebooks/blob/master/src/nelder-mead.md
    - https://math.stackexchange.com/questions/2447382/nelder-mead-function-fit-error-estimation-via-surface-fit
    - https://stats.stackexchange.com/questions/424073/calculate-the-uncertainty-of-a-mle

    Parameters
    ----------
    opt_func
        function that gets minimized
    fit_guess
        initial guess for minimization
    bounds
        bounds of the fitting parameters
    repeat
        how many times the least squares and minimize step gets repeated

    Returns
    -------
    opt_result: scipy.optimize.OptimizeResult
        the result of the optimization from the last step of Nelder-Mead.
    """
    initial_value = np.array(fit_guess)

    # least squares have different format for bounds
    ls_bounds_lb = [bound[0] for bound in bounds]
    ls_bounds_ub = [bound[1] for bound in bounds]
    ls_bounds = (ls_bounds_lb, ls_bounds_ub)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="overflow encountered in tanh")

        logger.debug(f"Started fitting routine")
        for i in range(repeat):
            logger.debug(f"Fitting routine pass {i}")
            opt_result = least_squares(
                opt_func,
                initial_value,
                bounds=ls_bounds,
                xtol=1e-13,
                max_nfev=1000,
                ftol=1e-9,
            )
            initial_value = opt_result.x
            logger.debug(f"Finished least squares")
            opt_result = minimize(
                opt_func,
                initial_value,
                bounds=bounds,
                tol=1e-13,
                options={"maxiter": 1e4, "fatol": 1e-9},
                method="Nelder-Mead",
            )
            initial_value = opt_result.x
            logger.debug(f"Finished Nelder-Mead")
    logger.debug(f"Finished fitting routine")
    return opt_result


@load_data("real", "imag", "freq")
def fit_circuit(
    real: pint.Quantity,
    imag: pint.Quantity,
    freq: pint.Quantity,
    circuit: str,
    initial_values: dict[str, float],
    output: str = "fit_circuit",
    fit_bounds: dict[str, tuple[float, float]] = None,
    fit_constants: list[str] = None,
    ignore_neg_res: bool = True,
    upper_freq: float = np.inf,
    lower_freq: float = 0,
    repeat: int = 1,
) -> dict[str, Union[int, str, pint.Quantity]]:
    """
    Fitting function for equivalent circuits of electrochemical impedance spectroscopy (EIS) data.

    For the fitting an equivalent circuit is needed, defined as a string. The circuit may be composed of multiple elements.
    To combine elements in series a dash (-) is used. Elements in parallel are wrapped by p( , ).
    An element is defined by an identifier (usually letters) followed by a digit.
    Already implemented elements are located in :class:`circuit_components<circuit_utils.circuit_components>`:

    +------------------------+--------+------------+---------------+--------------+
    | Name                   | Symbol | Parameters | Bounds        | Units        |
    +------------------------+--------+------------+---------------+--------------+
    | Resistor               | R      | R          | (1e-6, 1e6)   | Ohm          |
    +------------------------+--------+------------+---------------+--------------+
    | Capacitance            | C      | C          | (1e-20, 1)    | Farad        |
    +------------------------+--------+------------+---------------+--------------+
    | Constant Phase Element | CPE    | CPE_Q      | (1e-20, 1)    | Ohm^-1 s^a   |
    |                        |        +------------+---------------+--------------+
    |                        |        | CPE_a      | (0, 1)        |              |
    +------------------------+--------+------------+---------------+--------------+
    | Warburg element        | W      | W          | (0, 1e10)     | Ohm^-1 s^0.5 |
    +------------------------+--------+------------+---------------+--------------+
    | Warburg short element  | Ws     | Ws_R       | (0, 1e10)     | Ohm          |
    |                        |        +------------+---------------+--------------+
    |                        |        | Ws_T       | (1e-10, 1e10) | s            |
    +------------------------+--------+------------+---------------+--------------+
    | Warburg open element   | Wo     | Wo_R       | (0, 1e10)     | Ohm          |
    |                        |        +------------+---------------+--------------+
    |                        |        | Wo_T       | (1e-10, 1e10) | s            |
    +------------------------+--------+------------+---------------+--------------+

    Additionally an initial guess for the fitting parameters is needed.
    The initial guess is given as a dictionary where each key is the parameters name and
    the corresponding value is the guessed value for the circuit.

    The bounds of each parameter can be customized by the ``fit_bounds`` parameter.
    This parameter is a dictionary, where each key is the parameter name and the value consists of a tuple for the lower and upper bound (lb, ub).

    To hold a parameter constant, add the name of the parameter to a list and pass it as ``fit_constants``

    Parameters
    ----------
    real
        pint.Quantity containing the real part of the impedance data
        The unit of the provided data should be or gets converted to 'Ω'

    imag
        pint.Quantity containing the negative imaginary part of the impedance data
        The unit of the provided data should be or gets converted to 'Ω'

    freq
        pint.Quantitycontaining the frequency of the impedance data
        The unit of the provided data should be or gets converted to 'Hz'

    circuit
        Equivalent circuit for the fit

    initial_values
        dictionary with initial values
        Structure: {"param name": value, ... }

    output
        the name of the output

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


@load_data("freq")
def calc_circuit(
    freq: pint.Quantity,
    circuit: str,
    parameters: dict[str, float],
    output: str = "calc_circuit",
) -> tuple[dict[str, float], dict[str, str]]:
    """
    Calculate and adds the impedance as columns to the given dataframe for the given parameters, frequency and circuit.

    Parameters
    ----------
    circuit
        string describing the circuit. For more info see impedance.fit_circuit

    parameters
        dictionary with initial values
        Structure: {"param name": value, ... }

    output
        the name of the output

    freq
        numpy.ndarray or pint.Quantity of a numpy.ndarray containing the frequency
        The provided data should be in the unit of "Hz"

    Returns
    -------
    (parameters, units)
        A tuple containing two dicts.
         - values, containing the two lists of the real and the negative imaginary part of the impedance ce
         - units, contains the corresponding units of the impedance
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


@load_data("real", "imag")
def lowest_real_impedance(
    real: pint.Quantity,
    imag: pint.Quantity,
    output: str = "Zmin",
    threshold: float = 0.0,
) -> dict[str, Union[int, str, pint.Quantity]]:
    """
    Parameters
    ----------
    real
        numpy.ndarray or pint.Quantity of a numpy.ndarray containing the real part of
        the impedance data. The units of ``real`` and ``imag`` are assumed to match.

    imag
        numpy.ndarray or pint.Quantity of a numpy.ndarray containing the negative of the
        imaginary part of the impedance data. The units of ``real`` and ``imag`` are
        assumed to match.

    output
        The name of the output column, defaults to "Z".

    Returns
    -------
    (parameters, units): tuple[dict]
        A tuple containing a dictionary with the impedance, and the corresponding units
        of the real part of the impedance.
    """

    s = np.argsort(real)
    real = real[s]
    imag = imag[s]
    izeros = np.flatnonzero(imag < threshold)
    if izeros.size == 0:
        logger.warning(
            "No real impedance found. Returning real part of impedance "
            "with the smallest complex component."
        )
        iz = imag.argmin()
        z, u = real[iz].m, real[iz].u

    elif izeros[0] == 0:
        z, u = real[0].m, real[0].u
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
        z = ufloat(zv, ze)
        u = reu

    return {output: pint.Quantity(z, u)}
