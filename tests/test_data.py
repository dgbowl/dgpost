import pytest
import yadg.core
import json
import os

from tests.utils import datadir

def test_valid_datagram(datadir):
    os.chdir(datadir)
    with open("normalized.dg.json", "r") as infile:
        dg = json.load(infile)
    assert yadg.core.validators.validate_datagram(dg)

import dgpost.utils

def test_extract_(datadir):
    os.chdir(datadir)
    with open("normalized.dg.json", "r") as infile:
        dg = json.load(infile)
    df = dgpost.utils.extract(
        dg, 
        {
            "at": {"step": 0},
            "rawT": {"direct": {"key": "raw->T_f"}},
            "derT": {"direct": {"key": "derived->T"}},
            "xin": {"direct": {"key": "derived->xin->*"}}
        }
    )
    print(df.head())
    assert False