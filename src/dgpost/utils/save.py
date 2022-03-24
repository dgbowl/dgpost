"""
``save``: Save DataFrame as file.

The function :func:`dgpost.utils.save.save` processes the below specification
in order to save the given DataFrame:

.. code-block:: yaml

  save:
  - table: !!str      # table name from extract
    as:    !!str      # path of the new file
    type:  !!str      # optional file type - pkl, xlsx, csv, with the default
    being a pandas pickle.

.. code-author: Ulrich Sauter <ulrich.sauter@empa.ch>
"""
import json
import logging
import os
from yadg.dgutils.pintutils import ureg
from uncertainties import unumpy as unp

import pandas as pd

logger = logging.getLogger(__name__)


def save(table: pd.DataFrame, path: str, type: str = None, sigma: bool = True) -> None:
    """
    DataFrame saving function
    """
    if os.path.isdir(os.path.dirname(path)):
        logger.warning(f"save: Provided 'path' '{path}' does not exist.")

    # strip uncertainties if required
    if not sigma:
        logger.warning(f"save: Stripping uncertainties from table.")
        for col in table.columns:
            table[col] = unp.nominal_values(table[col].array)

    # find type of file in path or use default 'pkl'
    if type is None:
        type = os.path.splitext(path)[1][1:]
        if type is None or type == "":
            type = "pkl"

    # pkl and json store the whole dataframe

    if type == "pkl":
        table.to_pickle(path)
        return None
    elif type == "json":
        json_file = {
            "table": table.to_dict(),
            "attrs": table.attrs,
        }
        with open(path, "w") as f:
            json.dump(json_file, f, default=str)
        return None

    # for excel and csv the unit gets added to the column names

    units = table.attrs.get("units", {})
    names = {}

    for col in table.columns:
        unit = units.get(col, " ")
        if unit == " ":
            continue

        name = col + f" [{ureg.Unit(unit):~P}]"
        names[col] = name

    dframe = table.rename(columns=names).sort_index(axis=1)

    if type == "csv":
        dframe.to_csv(path)
    elif type == "xlsx":
        dframe.to_excel(path)
    else:
        raise ValueError(f"save: Provided 'type'  '{type}' is not supported.")
