"""
.. codeauthor::
    Peter Kraus

The function :func:`dgpost.utils.pivot.pivot` processes the below specification,
allowing the user to "pivot" a given :class:`pd.DataFrame` using specified column(s) as
additional indices:

.. _dgpost.recipe pivot:
.. autopydantic_model:: dgbowl_schemas.dgpost.recipe.Pivot

This feature is best illustrated using an below example. Consider an input
table in the following format:

.. list-table::
   :widths: 5 5 10 10
   :header-rows: 1

   * - `uts`
     - `index`
     - `frequency`
     - `impedance`
   * - 10000
     - 1
     - 1e9
     - 0.5700
   * - 10005
     - 1
     - 2e9
     - 0.5500
   * - 10010
     - 1
     - 4e9
     - 0.5000
   * - 10015
     - 1
     - 8e9
     - 0.4900
   * - 10020
     - 2
     - 1e9
     - 0.5740
   * - 10025
     - 2
     - 2e9
     - 0.5480
   * - 10030
     - 2
     - 4e9
     - 0.5000
   * - 10035
     - 2
     - 8e9
     - 0.4950

Here, the column ``index`` contains a numerical index of each impedance trace,
with a pair of ``frequency`` and ``impedance`` data in each row. However, for
post-processing in dgpost, it might be useful to re-order the data so that
the traces are grouped in each row:


.. list-table::
   :widths: 5 5 30 40
   :header-rows: 1

   * - `uts`
     - `index`
     - `frequency`
     - `impedance`
   * - 10000
     - 1
     - [1e9,    2e9,    4e9,    8e9]
     - [0.5700, 0.5500, 0.5000, 0.4900]
   * - 10020
     - 2
     - [1e9,    2e9,    4e9,    8e9]
     - [0.5740, 0.5480, 0.5000, 0.4950]

This can be achieved using the following code:

.. code:: python

  newdf = pivot(df, using="index", columns=["frequency", "impedance"], timestamp="first")

More documentation is provided in the :func:`~dgpost.utils.pivot.pivot`
function definition.

"""
import pandas as pd
import numpy as np
from typing import Union
from dgpost.utils.helpers import arrow_to_multiindex, get_units, set_units, key_to_tuple


def pivot(
    table: pd.DataFrame,
    using: Union[str, list[str]],
    columns: list[str] = None,
    timestamp: str = "first",
    timedelta: str = None,
) -> pd.DataFrame:
    """"""
    if isinstance(using, str):
        using = [using]

    mask = None
    for k in using:
        d = np.diff(np.ravel(table[k]), axis=0, append=np.inf)
        if mask is None:
            mask = d
        else:
            mask = np.logical_or(mask, d)
    indices = np.flatnonzero(mask)
    rows = []
    iname = table.index.name

    if columns is None:
        skipkeys = {iname, *using, *[key_to_tuple(k) for k in using]}
        columns = [k for k in table.columns if k not in skipkeys]

    for iidx, end in enumerate(indices):
        if iidx == 0:
            start = 0
        else:
            start = indices[iidx - 1] + 1
        slice = table.iloc[start : end + 1]
        row = {k: np.ravel(slice[k]) for k in columns}
        if timestamp == "first":
            row[iname] = slice.index[0]
        elif timestamp == "last":
            row[iname] = slice.index[-1]
        elif timestamp == "mean":
            row[iname] = np.mean(slice.index)
        if timedelta is not None:
            row[timedelta] = slice.index.array - row[iname]
        row.update({k: slice.iloc[0][k] for k in using})
        rows.append(row)

    newdf = pd.DataFrame.from_records(rows)
    newdf = newdf.set_index(iname)

    if "units" in table.attrs:
        units = {}
        for k in columns:
            u = get_units(k, table)
            set_units(k, u, units)
        if timedelta is not None:
            units[timedelta] = "s"
        newdf.attrs["units"] = units

    return arrow_to_multiindex(newdf)
