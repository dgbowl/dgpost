"""
``load``: Datagram and dataframe loading routine.

The function :func:`dgpost.utils.load.load` processes the below specification
in order to load the datagram json file:

.. code-block:: yaml

  load:
    - as:      !!str          # internal datagram or table name
      path:    !!str          # path to the datagram file
      check:   True           # whether the datagram is to be checked using ``yadg``

.. note::
    The key ``as`` are not processed by :func:`load`, they should be used by its caller 
    to store the returned ``datagram`` :class:`dict` into the correct variable.

.. code-author: Peter Kraus <peter.kraus@empa.ch>
"""
import os
import json
import pandas as pd
from yadg.core import validate_datagram
from uncertainties import ufloat_fromstr
import re
from typing import Union


def parse_ufloat(d: dict) -> dict:
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
    path: str, check: bool = True, type: str = "datagram"
) -> Union[dict, pd.DataFrame]:
    """
    Datagram and :class:`pd.DataFrame` loading function.

    Given the ``path`` to the datagram (json file) or the table (pkl or json file),
    this routine loads the object present at ``path``.
    """
    assert os.path.exists(path), f"Provided 'path' '{path}' does not exist."
    assert os.path.isfile(path), f"Provided 'path' '{path}' is not a file."

    if type == "datagram":
        with open(path, "r") as infile:
            dg = json.load(infile)
        if check:
            validate_datagram(dg)
        return dg
    else:
        if path.endswith("pkl"):
            df = pd.read_pickle(path)
            return df
        elif path.endswith("json"):
            with open(path, "r") as f:
                json_file = json.load(f, object_hook=parse_ufloat)
            df = pd.DataFrame.from_dict(json_file["table"])
            df.index = [float(i) for i in df.index]
            df.attrs.update(json_file["attrs"])
            return df
        else:
            raise RuntimeError(f"File type of '{path}' is not yet supported.")
