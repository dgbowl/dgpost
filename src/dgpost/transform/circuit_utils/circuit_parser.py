"""
dgpost.transform.circuit_utils.circuit_parser
=============================================
"""

import re
import warnings
import logging
from typing import Callable, Tuple
from scipy.optimize import least_squares, minimize


import numpy as np

from .circuit_components import circuit_components

logger = logging.getLogger(__name__)


def parse_circuit(
    circ: str,
) -> Tuple[list[dict], Callable[[dict, np.ndarray], np.ndarray]]:
    """Extended Backus–Naur form (EBNF) parser for a circuit string.

    Implements an extended Backus–Naur form (EBNF) to parse a string containing a description of a circuit.

    The syntax of the EBNF is given by:
        - circuit = element | element-circuit
        - element = component | parallel
        - parallel = p(circuit {,circuit})
        - component = a circuit component defined in ``circuit_components``

    So to put elements in series connect them through '-'
    Parallel elements are created by p(...,... ,...)

    To use a component in the circuit string use its symbol. The symbol can be followed by a digit to differentiate similar components.
    Already implemented circuit elements are located in :mod:`dgpost.transform.circuit_utils.circuit_components.py`.

    From this a function is generated and which evaluates the impedance of the circuit.

    Parameters
    ----------
    circ
        String describing a circuit

    Returns
    -------
    param_info
        list of used parameter. For more information about parameters look in ``circuit_components``
    calculate

    """

    param_info: list[dict] = []

    def component(c: str):
        # get and remove the name of the component from the circuit string
        match = re.match(r"([a-zA-Z]+)\d?", c)
        index = match.end()
        name = c[:index]
        c = c[index:]

        # get the symbol of the component and check if the component exists
        symbol = re.match("[A-Za-z]+", name).group()

        for key, comp in circuit_components.items():
            if comp.get_symbol() == symbol:
                break
        else:
            return c, 1

        # append the parameter to param info
        param_info.extend(comp.get_parameters(name))

        # return the circuit string and return a string for later evaluation
        return c, key + rf".calc_impedance(param,'{name}', omega)"

    def parallel(c: str):
        c = c[2:]
        tot_eq = ""
        while not c.startswith(")"):
            if c.startswith(","):
                c = c[1:]
            c, eq = circuit(c)
            if tot_eq:
                tot_eq += " + "
            tot_eq += f"1.0 / ({eq})"
        c = c[1:]
        return c, f"1.0 / ({tot_eq})"

    def element(c: str):
        if c.startswith("p("):
            c, eq = parallel(c)
        else:
            c, eq = component(c)
        return c, eq

    def circuit(c: str):
        if not c:
            return c, ""
        c, eq = element(c)
        tot_eq = f"{eq}"
        if c.startswith("-"):
            c, eq = circuit(c[1:])
            tot_eq += f" + {eq}"
        return c, tot_eq

    __, equation = circuit(circ.replace(" ", ""))

    calculate = eval("lambda param, omega: " + equation, circuit_components.copy())
    return param_info, calculate


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

        logger.debug("Started fitting routine")
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
            logger.debug("Finished least squares")
            opt_result = minimize(
                opt_func,
                initial_value,
                bounds=bounds,
                tol=1e-13,
                options={"maxiter": 1e4, "fatol": 1e-9},
                method="Nelder-Mead",
            )
            initial_value = opt_result.x
            logger.debug("Finished Nelder-Mead")
    logger.debug("Finished fitting routine")
    return opt_result
