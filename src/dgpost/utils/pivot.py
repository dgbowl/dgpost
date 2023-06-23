"""
**pivot**: Reorder tables using columns.
--------------------------------------------------------
.. codeauthor::
    Peter Kraus


"""
import pandas as pd
import numpy as np


def pivot(
    table: pd.DataFrame,
    on: str,
    columns: list[str] = None,
    timestamp: str = "first",
) -> pd.DataFrame:
    """"""

    indices = list(np.flatnonzero(np.diff(table[on]))) + [-1]
    rows = []
    iname = table.index.name

    if columns is None:
        columns = [k for k in table.columns if k not in {on, iname}]

    for iidx, end in enumerate(indices):
        if iidx == 0:
            start = 0
        else:
            start = indices[iidx - 1] + 1
        slice = table.iloc[start:end]
        row = {k: slice[k].to_numpy() for k in columns}
        if timestamp == "first":
            row[iname] = slice.index[0]
        elif timestamp == "last":
            row[iname] = slice.index[-1]
        elif timestamp == "mean":
            row[iname] = np.mean(slice.index)

    row[on] = slice[on].iloc[0]
    rows.append(row)

    newdf = pd.DataFrame.from_records(rows)
    newdf = newdf.set_index(iname)

    return newdf
