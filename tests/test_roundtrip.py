import pytest
import os
import pandas as pd

import dgpost.utils
from copy import deepcopy
from .utils import compare_dfs


@pytest.mark.parametrize(
    "filetype",
    ["json", "pkl"],
)
@pytest.mark.parametrize(
    "input",
    [
        (  # ts0 - load dg, with check, simple extract
            {"path": "sparse.dg.json", "type": "datagram"},
            {"at": {"step": "a"}, "columns": [{"key": "raw->T_f", "as": "T"}]},
        ),
        (  # ts1 - load dg, with check, starred extract
            {"path": "normalized.dg.json", "type": "datagram"},
            {"at": {"step": "a"}, "columns": [{"key": "derived->xin->*", "as": "xin"}]},
        ),
        (  # ts2 - load dg, with check, multiple extracts, implicit starred
            {"path": "normalized.dg.json", "type": "datagram"},
            {
                "at": {"step": "a"},
                "columns": [
                    {"key": "derived->xin", "as": "xin"},
                    {"key": "raw->T_f", "as": "T"},
                ],
            },
        ),
        (  # ts3 - load df, multiple extracts, implicit starred
            {"path": "normalized.df.pkl", "type": "table"},
            {
                "columns": [
                    {"key": "xin", "as": "xin_l"},
                    {"key": "T", "as": "T_l"},
                ],
            },
        ),
    ],
)
def test_roundtrip_direct(input, filetype, datadir):
    os.chdir(datadir)
    l, e = deepcopy(input)
    outpath = f"out.{l['path']}.{filetype}"
    dg = dgpost.utils.load(**l)
    ref = dgpost.utils.extract(dg, spec=e)
    dgpost.utils.save(table=ref, path=outpath, type=filetype)

    assert os.path.exists(outpath)
    df = dgpost.utils.load(**{"path": outpath, "type": "table"})
    compare_dfs(ref, df)


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
