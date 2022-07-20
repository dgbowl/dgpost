import pytest
import json
import os
import pandas as pd

import dgpost.utils
from .utils import compare_dfs


@pytest.mark.parametrize(
    "input",
    [
        {  # ts0 - load with check = True
            "path": "sparse.dg.json",
            "check": True,
        },
        {  # ts1 - load with check = False
            "path": "normalized.dg.json",
            "check": False,
        },
        {  # ts2 - load without check
            "path": "sparse.dg.json",
        },
    ],
)
def test_load_datagram(input, datadir):
    os.chdir(datadir)
    ret = dgpost.utils.load(**input)
    with open(input["path"], "r") as infile:
        ref = json.load(infile)
    assert ret == ref


@pytest.mark.parametrize(
    "spec, outfile",
    [
        [  # ts0 - load v1.0 table with "->" without units
            {"path": "flowcx.float.df.pkl"},
            "ref.flowcx.float.df.pkl",
        ],
        [  # ts1 - load v1.0 table with "->" and with "->" units
            {"path": "flowcx.units.float.df.pkl"},
            "ref.flowcx.units.float.df.pkl",
        ],
        [  # ts2 - roundtrip table with flat columns and units
            {"path": "Ewe_I.df.pkl"},
            "Ewe_I.df.pkl",
        ],
        [  # ts3 - load v1.0 table with a mixture of "->"
            {"path": "2022_02_22.df.GC+flow+I.pkl"},
            "ref.df.GC+flow+I.pkl",
        ],
        [  # ts4 - roundtrip test
            {"path": "ref.df.GC+flow+I.pkl"},
            "ref.df.GC+flow+I.pkl",
        ],
    ],
)
def test_load_table(spec, outfile, datadir):
    os.chdir(datadir)
    df = dgpost.utils.load(**spec, type="table")
    print(f"{df.head()=}")
    print(f"{df.attrs=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df)
