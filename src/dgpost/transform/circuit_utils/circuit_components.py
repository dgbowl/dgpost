"""
dgpost.transform.circuit_utils.circuit_components
=================================================
"""

from typing import Type

import numpy as np


def create_parameter(name: str, bounds: tuple[float, float], unit: str):
    """
    Creates a dictionary with keys `name`, `bounds` and `unit`

    Parameters
    ----------
    name
        name of the parameter
    bounds
        default bounds of the parameter
    unit
        SI unit of the parameter

    Returns
    -------
    dict
        dictionary containing the input values
    """
    return {"name": name, "bounds": bounds, "unit": unit}


class Component:
    """
    A component stores information needed for the fitting.
    """

    @staticmethod
    def get_symbol() -> str:
        """
        Unique symbol used to identify the component in the circuit string

        The symbol can only contain letters, i.e. a-z, A-Z
        """
        raise NotImplementedError

    @staticmethod
    def get_parameters(name: str) -> list[dict]:
        """
        returns the parameter(s) that describe the component

        A parameter is a dictionary with the keys: `name`, `bounds` and `unit`.
        The `name` of the parameter should be based on the symbol. It can also contain any character except a whitespace.
        The `bounds` are given as a tuple with the lower (`lb`) and upper bounds (`ub`) like `(lb, ub)`.
        The unit needs to be recognised by pint

        Parameters
        ----------
        name
            name of the component in the circuit string, made out of the symbol with an additional digit.

        Returns
        -------
        list[dict]
            The parameters that describes the component.
            A parameter is a dictionary with 3 keys: 'name', 'bounds' and 'unit'
        """
        raise NotImplementedError

    @staticmethod
    def calc_impedance(param: dict[str, float], name: str, freq: np.array) -> np.array:
        """
        Calculates the impedance of the component

        Parameters
        ----------
        param
            dictionary of parameter values with the name as the key
        name
            the name of the component
        freq
            the frequencies at which the impedance should be calculated

        Returns
        -------
        np.array
            numpy array with the complex impedance of the component for the given frequencies
        """
        raise NotImplementedError

    def __repr__(self):
        return f"Component {self.get_symbol()}"


class Resistor(Component):
    """defines a resistor"""

    @staticmethod
    def get_symbol():
        return "R"

    @staticmethod
    def get_parameters(name):
        param = create_parameter(name, (1e-6, 1e6), "Ω")
        return [param]

    @staticmethod
    def calc_impedance(param, name, freq):
        result = np.full_like(freq, param.get(name), dtype=float)
        return result


class Capacitor(Component):
    """defines a capacitor"""

    @staticmethod
    def get_symbol():
        return "C"

    @staticmethod
    def get_parameters(name):
        param = create_parameter(name, (1e-20, 1), "F")
        return [param]

    @staticmethod
    def calc_impedance(param, name, freq):
        value = param.get(name)
        result = 1.0 / (1j * 2 * np.pi * freq * value)
        return np.array(result)


class CPE(Component):
    """defines a constant phase element"""

    @staticmethod
    def get_symbol():
        return "CPE"

    @staticmethod
    def get_parameters(name):
        param1 = create_parameter(name + "_Q", (1e-20, 1), "Ω^-1 s^a")
        param2 = create_parameter(name + "_a", (0, 1), "")
        return [param1, param2]

    @staticmethod
    def calc_impedance(param, name, freq):
        # Zcpe = 1 / Q(jωᵃ) = jω⁻ᵃ / Q
        q = param.get(name + "_Q")
        n = param.get(name + "_a")
        result = (1j * 2 * np.pi * freq) ** (-n) / q
        return np.array(result)


class Warburg(Component):
    """defines a semi-infinite Warburg element"""

    @staticmethod
    def get_symbol():
        return "W"

    @staticmethod
    def get_parameters(name):
        param = create_parameter(name, (0, 1e10), "Ω s^(-1/2)")
        return [param]

    @staticmethod
    def calc_impedance(param, name, freq):
        # Zw = [σω⁻¹ᐟ² - j(σω⁻¹ᐟ²)] = σ(1-j) / ω¹ᐟ²
        value = param.get(name)
        result = value * (1 - 1j) / np.sqrt(2 * np.pi * freq)
        return np.array(result)


class WarburgOpen(Component):
    """defines a finite-space Warburg element"""

    @staticmethod
    def get_symbol():
        return "Wo"

    @staticmethod
    def get_parameters(name):
        param1 = create_parameter(name + "_R", (0, 1e10), "Ω")
        param2 = create_parameter(name + "_T", (1e-10, 1e10), "s")
        return [param1, param2]

    @staticmethod
    def calc_impedance(param, name, freq):
        r = param.get(name + "_R")
        t = param.get(name + "_T")
        alpha = np.sqrt(1j * t * 2 * np.pi * freq)
        result = r / alpha / np.tanh(alpha)
        return np.array(result)


class WarburgShort(Component):
    """defines a finite-length Warburg element"""

    @staticmethod
    def get_symbol():
        return "Ws"

    @staticmethod
    def get_parameters(name):
        param1 = create_parameter(name + "_R", (0, 1e10), "Ω")
        param2 = create_parameter(name + "_T", (1e-10, 1e10), "s")
        return [param1, param2]

    @staticmethod
    def calc_impedance(param, name, freq):
        r = param.get(name + "_R")
        t = param.get(name + "_T")
        alpha = np.sqrt(1j * t * 2 * np.pi * freq)
        result = r / alpha * np.tanh(alpha)
        return np.array(result)


circuit_components: dict[str, Type[Component]] = {
    "Resistor": Resistor,
    "Capacitor": Capacitor,
    "CPE": CPE,
    "Warburg": Warburg,
    "WarburgShort": WarburgShort,
    "WarburgOpen": WarburgOpen,
}
