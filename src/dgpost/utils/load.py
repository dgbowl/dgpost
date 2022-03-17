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


def load(path: str, check: bool = True, type: str = "datagram") -> dict:
    """
    Datagram and dataframe loading function.

    Given the ``path`` to the datagram json file, this routine
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
        else:
            raise RuntimeError(f"File type of '{path}' is not yet supported.")
