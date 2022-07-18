"""
**load**: Datagram and table loading routine
--------------------------------------------
.. codeauthor:: 
    Ueli Sauter, 
    Peter Kraus
    
The function :func:`dgpost.utils.load.load` processes the below specification
in order to load the datagram json file:

.. _dgpost.recipe load:
.. autopydantic_model:: dgbowl_schemas.dgpost.recipe_1_1.load.Load

.. note::

    The key ``as`` is not processed by :func:`load`, it should be used by its caller 
    to store the returned `datagram` or :class:`pd.DataFrame` into the correct variable.

"""
import os
import json
import pandas as pd
from yadg.core import validate_datagram
from uncertainties import ufloat_fromstr
import re
from typing import Union
import logging
from dgpost.utils.helpers import arrow_to_multiindex

logger = logging.getLogger(__name__)


def _parse_ufloat(d: dict) -> dict:
    ret = {}
    for k, v in d.items():
        new_v = v
        if type(v) is str:
            # match for ufloat
            if re.match(r"[0-9\.]+\+/-[0-9\.]+", v):
                new_v = ufloat_fromstr(v)
        ret[k] = new_v
    return ret


def load(
    path: str,
    check: bool = True,
    type: str = "datagram",
) -> Union[dict, pd.DataFrame]:
    """"""
    assert os.path.exists(path), f"Provided 'path' '{path}' does not exist."
    assert os.path.isfile(path), f"Provided 'path' '{path}' is not a file."

    if type == "datagram":
        logger.debug("loading datagram from '%s'" % path)
        with open(path, "r") as infile:
            dg = json.load(infile)
        if check:
            validate_datagram(dg)
        return dg
    else:
        logger.debug("loading table from '%s'" % path)
        if path.endswith("pkl"):
            df = pd.read_pickle(path)
            df.sort_index(axis="index", inplace=True)
        elif path.endswith("json"):
            with open(path, "r") as f:
                json_file = json.load(f, object_hook=_parse_ufloat)
            df = pd.DataFrame.from_dict(json_file["table"])
            df.sort_index(axis="index", inplace=True)
            df.index = [float(i) for i in df.index]
            df.attrs.update(json_file["attrs"])
        else:
            raise RuntimeError(f"File type of '{path}' is not yet supported.")

        return arrow_to_multiindex(df)
