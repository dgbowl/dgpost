import pytest
import json
import os

import dgpost.utils


@pytest.mark.parametrize(
    "input",
    [
        {"path": "sparse.dg.json", "check": True,},  # ts0 - load with check = True
        {  # ts1 - load with check = False
            "path": "normalized.dg.json",
            "check": False,
        },
        {"path": "sparse.dg.json",},  # ts2 - load without check
    ],
)
def test_load(input, datadir):
    os.chdir(datadir)
    ret = dgpost.utils.load(**input)
    with open(input["path"], "r") as infile:
        ref = json.load(infile)
    assert ret == ref
