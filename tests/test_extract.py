import pytest
import yadg.core
import json
import os
import pandas as pd

from tests.utils import datadir
import dgpost.utils


def test_valid_datagram(datadir):
    os.chdir(datadir)
    with open("normalized.dg.json", "r") as infile:
        dg = json.load(infile)
    assert yadg.core.validators.validate_datagram(dg)


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - read in & rename data from a defined step using index
            "normalized.dg.json",
            {
                "at": {"index": 0},
                "direct": [
                    {"key": "raw->T_f", "as": "rawT"},
                    {"key": "derived->T", "as": "derT"},
                ],
            },
            "direct.single.pkl",
        ),
        (  # ts1 - read in & rename data from a defined step using tag
            "normalized.dg.json",
            {
                "at": {"step": "a"},
                "direct": [
                    {"key": "raw->T_f", "as": "rawT"},
                    {"key": "derived->T", "as": "derT"},
                ],
            },
            "direct.single.pkl",
        ),
        (  # ts2 - read in & rename data from multiple steps using indices
            "normalized.dg.json",
            {
                "at": {"indices": [1, 2, 3]},
                "direct": [{"key": "derived->xout->O2", "as": "O2"}],
            },
            "direct.multiple.pkl",
        ),
        (  # ts3 - read in & rename data from multiple steps using tags
            "normalized.dg.json",
            {
                "at": {"steps": ["b1", "b2", "b3"]},
                "direct": [{"key": "derived->xout->O2", "as": "O2"}],
            },
            "direct.multiple.pkl",
        ),
        (  # ts4 - read in a dict using *
            "normalized.dg.json",
            {
                "at": {"indices": [1, 2, 3]},
                "direct": [{"key": "derived->xout->*", "as": "xout"}],
            },
            "direct.starred.pkl",
        ),
        (  # ts5 - read in a dict with sparse keys
            "sparse.dg.json",
            {
                "at": {"indices": [1, 2, 3]},
                "direct": [
                    {"key": "derived->xout->propane", "as": "propane"},
                    {"key": "derived->xout->propylene", "as": "propylene"},
                ],
            },
            "direct.sparse.pkl",
        ),
        (  # ts6 - read in a dict using * with list as values
            "normalized.dg.json",
            {
                "at": {"step": "c"},
                "direct": [
                    {"key": "raw->traces->FID->*", "as": "traces->FID"},
                    {"key": "raw->traces->TCD->*", "as": "traces->TCD"},
                ],
            },
            "direct.traces.pkl",
        ),
        (  # ts7 - read in a dict[dict] using * with list as values
            "normalized.dg.json",
            {
                "at": {"step": "c"},
                "direct": [{"key": "raw->traces->*", "as": "traces"}],
            },
            "direct.traces.pkl",
        ),
        (  # ts8 - interpolate explicit variable on one step
            "normalized.dg.json",
            {
                "at": {"step": "b1"},
                "direct": [{"key": "derived->xout->O2", "as": "xout->O2"}],
                "interpolated": [
                    {"key": "derived->xin->O2", "as": "xin->O2", "keyat": {"step": 0}}
                ],
            },
            "interpolated.single.pkl",
        ),
        (  # ts9 - interpolate explicit variable on multiple steps
            "normalized.dg.json",
            {
                "at": {"indices": [1, 2, 3]},
                "direct": [{"key": "derived->xout->O2", "as": "xout->O2"}],
                "interpolated": [
                    {"key": "derived->xin->O2", "as": "xin->O2", "keyat": {"step": "a"}}
                ],
            },
            "interpolated.multiple.pkl",
        ),
        (  # ts10 - interpolate a dict using * on multiple steps
            "normalized.dg.json",
            {
                "at": {"indices": [1, 2, 3]},
                "direct": [{"key": "derived->xout->*", "as": "xout"}],
                "interpolated": [
                    {"key": "derived->xin->*", "as": "xin", "keyat": {"step": "a"}}
                ],
            },
            "interpolated.starred.pkl",
        ),
        (  # ts11 - constant with float, str(ufloat) values
            "normalized.dg.json",
            {
                "at": {"indices": [1, 2, 3]},
                "constant": [
                    {"as": "mass", "value": 6.35, "units": "kg"},
                    {"as": "element", "value": 12},
                    {"as": "volume", "value": "5.546(0)", "units": "l"},
                ],
            },
            "constant.multiple.pkl",
        ),
        (  # ts12 - constant with float, str(ufloat) values
            "normalized.dg.json",
            {
                "at": {"timestamps": [1575360000.0 + i * 200.0 for i in range(10)]},
                "constant": [{"as": "volume", "value": "5.546(0)", "units": "l"},],
                "interpolated": [
                    {"key": "derived->xin->O2", "as": "xin->O2", "keyat": {"step": "a"}}
                ],
            },
            "interpolated.timestamps.pkl",
        ),
    ],
)
def test_extract(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    with open(inpath, "r") as infile:
        dg = json.load(infile)
    df = dgpost.utils.extract(dg, spec)
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)
    assert ref.attrs == df.attrs
