"""
.. codeauthor::
    Ueli Sauter,
    Peter Kraus

The function :func:`dgpost.utils.save.save` processes the below specification
in order to save the given DataFrame:

.. _dgpost.recipe save:
.. autopydantic_model:: dgbowl_schemas.dgpost.recipe.Save

.. note::

    Metadata, including the `recipe` used to create the saved file, as well as
    provenance information about the version of dgpost used to process the
    `recipe` are saved into the ``df.attrs["meta"]`` entry and therefore only
    available in ``pkl`` or ``json`` exports.

"""
import json
import os
from uncertainties import unumpy as unp
from importlib import metadata
import pandas as pd
import logging
import pint

from dgpost.utils.helpers import get_units

logger = logging.getLogger(__name__)


def save(
    table: pd.DataFrame,
    path: str,
    type: str = None,
    columns: list[str] = None,
    sigma: bool = True,
    meta: dict = None,
) -> None:
    """"""
    if meta is None:
        meta = {"provenance": f"dgpost-{metadata.version('dgpost')}"}

    folder = os.path.dirname(path)
    if os.path.isdir(folder) or folder == "":
        pass
    else:
        raise ValueError(f"Parent folder '{folder}' provided in 'path' does not exist.")

    if columns is None:
        pass
    else:
        cols = []
        for col in columns:
            if col not in table.columns:
                logger.warning(
                    f"Column '{col}' is not present in table and will not be exported."
                )
            else:
                cols.append(col)
        table = table[cols]

    # strip uncertainties if required
    if not sigma:
        logger.warning(f"Stripping uncertainties from table.")
        for col in table.columns:
            try:
                table[col] = unp.nominal_values(table[col].array)
            except ValueError:
                logger.warning(
                    f"Cannot strip uncertainties from array quantity '{col}'."
                )

    # find type of file in path or use default 'pkl'
    if type is None:
        type = os.path.splitext(path)[1][1:]
        if type is None or type == "":
            type = "pkl"

    # pkl and json store the whole dataframe
    if type == "pkl":
        logger.debug("Writing pickle into '%s'." % path)
        table.attrs["meta"] = meta
        table.to_pickle(path)
        return None
    elif type == "json":
        logger.debug("Writing json into '%s'." % path)
        table.attrs["meta"] = meta
        json_file = {
            "table": table.to_dict(orient="tight"),
            "attrs": table.attrs,
        }
        with open(path, "w") as f:
            json.dump(json_file, f, default=str)
        return None

    # for excel and csv the unit gets added to the column names
    names = []
    for col in table.columns:
        unit = get_units(col, table)
        col = [c if isinstance(c, str) else "" for c in col]
        if unit is None:
            names.append(col)
        else:
            names.append((col[0] + f" [{pint.Unit(unit):~P}]", *col[1:]))

    savedf = table.copy()
    if all([isinstance(name, str) for name in names]):
        savedf.columns = pd.Index(names)
    else:
        savedf.columns = pd.MultiIndex.from_tuples(names)
    savedf = savedf.sort_index(axis="columns")
    if type == "csv":
        logger.debug("Writing csv into '%s'." % path)
        savedf.to_csv(path)
    elif type == "xlsx":
        logger.debug("Writing xlsx into '%s'." % path)
        savedf.to_excel(path)
    else:
        raise ValueError(f"save: Provided 'type' '{type}' is not supported.")
