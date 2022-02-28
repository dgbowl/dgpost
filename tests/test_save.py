import json
import os
import re

import dgpost.utils
import pandas as pd
import pytest
from uncertainties import ufloat_fromstr

from tests.utils import datadir


def parse_ufloat(d):
    for k, v in d.items():
        new_v = v
        if type(v) is str:
            # match for ufloat
            if re.match(r"[0-9\.]+\+/-[0-9\.]+", v):
                new_v = ufloat_fromstr(v)

        d[k] = new_v
    return d


def load_files(path: str) -> pd.DataFrame:
    filetype = os.path.splitext(path)[1][1:]
    if filetype == "pkl":
        df = pd.read_pickle(path)
    elif filetype == "json":
        with open(path, "r") as f:
            json_file = json.load(f, object_hook=parse_ufloat)
            df = pd.DataFrame.from_dict(json_file["table"])
            df.attrs.update(json_file["attrs"])
    elif filetype == "csv":
        df = pd.read_csv(path, index_col=0)
    elif filetype == "xlsx":
        df = pd.read_excel(path, index_col=0)
    else:
        raise ValueError(f"save: Provided 'type'  '{type}' is not supported.")
    return df


@pytest.mark.parametrize(
    "filetype",
    [
        # ts0 - save dataframe as pickle
        "pkl",
        # ts1 - save dataframe as csv
        "csv",
        # ts2 - save dataframe as csv
        "xlsx",
        # ts3 - save dataframe as json
        "json",
    ],
)
@pytest.mark.parametrize(
    "table",
    [
        # ts0 - dataframe with float values
        "flowcx.float.df.pkl",
        # ts1 - dataframe with ufloat values
        "flowcx.ufloat.df.pkl",
        # ts2 - dataframe with float values and units
        "flowcx.units.float.df.pkl",
        # ts3 - dataframe with ufloat values and units
        "flowcx.units.ufloat.df.pkl",
    ],
)
def test_save(table, filetype, datadir):
    os.chdir(datadir)
    path = f"saved.{table.replace('pkl', filetype)}"
    dgpost.utils.save(table=pd.read_pickle(table), path=path, type=filetype)

    # check if the two files are the same
    df = load_files(path)
    ref = load_files(f"control.{path}")

    pd.testing.assert_frame_equal(df, ref, check_like=True)
    assert df.attrs == ref.attrs
