import re
from typing import Callable, Tuple

from numpy import ndarray

from .circuit_components import circuit_components


def parse_circuit(
    circ: str,
) -> Tuple[list[dict], Callable[[dict, ndarray], ndarray]]:
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
