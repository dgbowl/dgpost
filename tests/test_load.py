import pytest
import yadg.core
import json
import os
import pandas as pd

from tests.utils import datadir
import dgpost.utils


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
def test_load(input, datadir):
    os.chdir(datadir)
    ret = dgpost.utils.load(**input)
    with open(input["path"], "r") as infile:
        ref = json.load(infile)
    assert ret == ref
