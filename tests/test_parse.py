import pytest
import yadg.core
import json
import os
import pandas as pd

from tests.utils import datadir
import dgpost.utils


@pytest.mark.parametrize(
    "inpath, spec",
    [
        (  # ts0 - load, single item, windows path, default check == True
            "load_1.yaml",
            {
                "load": [
                    {
                        "as": "sparse",
                        "path": r"C:\Users\krpe\postprocess\tests\common\sparse.dg.json",
                        "check": True,
                    }
                ]
            },
        ),
        (  # ts1 - load, multiple items, explicit check
            "load_2.yaml",
            {
                "load": [
                    {"as": "sparse", "path": "sparse.dg.json", "check": True},
                    {"as": "normalized", "path": "normalized.dg.json", "check": False},
                ]
            },
        ),
        (  # ts2 - load, single item, unix path, different order
            "load_3.yaml",
            {
                "load": [
                    {
                        "as": "normalized",
                        "path": "/home/test/normalized.dg.json",
                        "check": True,
                    },
                ]
            },
        ),
        (  # ts3 - extract, 2 direct elements
            "extract_1.yaml",
            {
                "extract": [
                    {
                        "as": "table 1",
                        "from": "sparse",
                        "at": {"step": "a"},
                        "direct": [
                            {"key": "raw->T_f", "as": "rawT"},
                            {"key": "derived->T", "as": "derT"},
                        ],
                    },
                ]
            },
        ),
        (  # ts4 - extract, 1 constant element, value as str
            "extract_2.yaml",
            {
                "extract": [
                    {
                        "as": "table 2",
                        "from": "norm",
                        "at": {"indices": [1, 2, 3]},
                        "constant": [{"value": "5.0", "as": "mass"}],
                    },
                ]
            },
        ),
        (  # ts5 - extract, 1 interpolated element
            "extract_3.yaml",
            {
                "extract": [
                    {
                        "as": "table 2",
                        "from": "norm",
                        "at": {"steps": ["b1", "b2", "b3"]},
                        "interpolated": [
                            {
                                "key": "derived->xin->*",
                                "as": "xin",
                                "keyat": {"step": "a"},
                            }
                        ],
                    },
                ]
            },
        ),
        (  # ts6 - transform, multiple using, False as string
            "transform_1.yaml",
            {
                "transform": [
                    {
                        "table": "t1",
                        "with": "catalysis.conversion",
                        "using": [
                            {"feedstock": "propane", "product": "False"},
                            {"feedstock": "C3H8", "element": "C"},
                        ],
                    },
                ]
            },
        ),
    ],
)
def test_parse(inpath, spec, datadir):
    os.chdir(datadir)
    ret = dgpost.utils.parse(inpath)
    assert ret == spec
