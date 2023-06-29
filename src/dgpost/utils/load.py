"""
.. codeauthor::
    Ueli Sauter,
    Peter Kraus

The function :func:`dgpost.utils.load.load` processes the below specification
in order to load the datagram json file:

.. _dgpost.recipe load:
.. autopydantic_model:: dgbowl_schemas.dgpost.recipe.Load

.. note::

    The key ``as`` is not processed by :func:`load`, it should be used by its caller
    to store the returned `datagram` or :class:`pd.DataFrame` into the correct variable.

"""
import os
import json
import pandas as pd
from uncertainties import ufloat_fromstr, UFloat
from typing import Union, Any
import logging
from dgpost.utils.helpers import arrow_to_multiindex
import datatree

logger = logging.getLogger(__name__)


def _parse_ufloat(v: Union[str, Any]) -> Union[UFloat, Any]:
    if isinstance(v, str):
        try:
            return ufloat_fromstr(v)
        except ValueError:
            return v
    else:
        return v


def load(
    path: str,
    check: bool = None,
    type: str = "netcdf",
) -> Union[dict, pd.DataFrame]:
    """"""
    assert os.path.exists(path), f"Provided 'path' '{path}' does not exist."
    assert os.path.isfile(path), f"Provided 'path' '{path}' is not a file."

    if type.lower() == "netcdf":
        logger.debug("loading a NetCDF file from '%s'" % path)
        return datatree.open_datatree(path, engine="h5netcdf")
    elif type.lower() == "datagram":
        logger.debug("loading datagram from '%s'" % path)
        with open(path, "r") as infile:
            dg = json.load(infile)
        if check is not None:
            logger.warning(
                "The 'check' argument has been deprecated and will "
                "stop working in dgpost-3.0."
            )
        return dg
    elif type.lower() == "table":
        logger.debug("loading table from '%s'" % path)
        if path.endswith("pkl"):
            df = pd.read_pickle(path)
        elif path.endswith("json"):
            with open(path, "r") as f:
                json_data = json.load(f)
            table = json_data["table"]
            attrs = json_data["attrs"]
            for i, v in enumerate(table["data"]):
                table["data"][i] = [_parse_ufloat(vv) for vv in v]
            df = pd.DataFrame.from_dict(table, orient="tight")
            df.index = [float(i) for i in df.index]
            df.attrs.update(attrs)
        else:
            raise RuntimeError(f"File type of '{path}' is not yet supported.")

        return arrow_to_multiindex(df)
