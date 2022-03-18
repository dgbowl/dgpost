import pytest
import yadg.core
import json
import os
import pandas as pd

from tests.utils import datadir
import dgpost.utils
from copy import deepcopy


@pytest.mark.parametrize(
    "filetype",
    ["json", "pkl"],
)
@pytest.mark.parametrize(
    "input",
    [
        (  # ts0 - load with check = True
            {"path": "sparse.dg.json"},
            {"at": {"step": "a"}, "columns": [{"key": "raw->T_f", "as": "T"}]},
        )
    ],
)
def test_roundtrip_direct(input, filetype, datadir):
    os.chdir(datadir)
    l, e = deepcopy(input)
    outpath = l["path"] + "." + filetype
    dg = dgpost.utils.load(**l)
    df = dgpost.utils.extract(dg, spec=e)
    dgpost.utils.save(table=df, path=outpath, type=filetype)

    assert os.path.exists(outpath)
    ret = dgpost.utils.load(**{"path": outpath, "type": "table"})

    pd.testing.assert_frame_equal(df, ret, check_like=True)
    assert df.attrs == ret.attrs


@pytest.mark.parametrize(
    "filetype",
    ["json", "pkl"],
)
@pytest.mark.parametrize(
    "input",
    ["les_1.yaml"],
)
def test_roundtrip_via_yaml(input, filetype, datadir):
    os.chdir(datadir)
    dgs, tabs = dgpost.run(input)
    df = tabs["df"]
    outpath = "sparse.dg.json" + "." + filetype
    assert os.path.exists(outpath)
    ret = dgpost.utils.load(**{"path": outpath, "type": "table"})

    pd.testing.assert_frame_equal(df, ret, check_like=True)
    assert df.attrs == ret.attrs
