import os
import pytest
import pandas as pd
import numpy as np
import pint

from dgpost.transform import table
from dgpost.utils import transform
from .utils import compare_dfs


@pytest.mark.parametrize(
    "a, b, output",
    [
        (  # ts0 - sum
            pint.Quantity(6.0, "ml/min"),
            pint.Quantity(0.6, "l/h"),
            {"c": pint.Quantity(16.0, "ml/min")},
        ),
        (  # ts1 - sum with nan
            pint.Quantity(float("NaN"), "ml/min"),
            pint.Quantity(0.6, "l/h"),
            {"c": pint.Quantity(10.0, "ml/min")},
        ),
    ],
)
def test_table_combine_columns_direct(a, b, output):
    ret = table.combine_columns(a=a, b=b, output="c")
    for k, v in ret.items():
        assert np.allclose(v, output[k])


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - explicit as well as default output
            "test.electro.pkl",
            [
                {"a": "I", "b": "<I>", "output": "c"},
                {"a": "Ewe", "b": "<Ewe>"},  # should default to Ewe
            ],
            "ref.electro.pkl",
        ),
    ],
)
def test_table_combine_columns_df(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(inpath)
    df = transform(df, "table.combine_columns", using=spec)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outpath)
    print(f"{ref.head()=}")
    df.to_pickle(outpath)
    compare_dfs(ref, df)
