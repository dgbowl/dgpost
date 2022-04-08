import pytest
import yadg.core
import json
import os
import pandas as pd

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
                "columns": [
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
                "columns": [
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
                "columns": [{"key": "derived->xout->O2", "as": "O2"}],
            },
            "direct.multiple.pkl",
        ),
        (  # ts3 - read in & rename data from multiple steps using tags
            "normalized.dg.json",
            {
                "at": {"steps": ["b1", "b2", "b3"]},
                "columns": [{"key": "derived->xout->O2", "as": "O2"}],
            },
            "direct.multiple.pkl",
        ),
        (  # ts4 - read in a dict using *
            "normalized.dg.json",
            {
                "at": {"indices": [1, 2, 3]},
                "columns": [{"key": "derived->xout->*", "as": "xout"}],
            },
            "direct.starred.pkl",
        ),
        (  # ts5 - read in a dict with sparse keys
            "sparse.dg.json",
            {
                "at": {"indices": [1, 2, 3]},
                "columns": [
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
                "columns": [
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
                "columns": [{"key": "raw->traces->*", "as": "traces"}],
            },
            "direct.traces.pkl",
        ),
        (  # ts8 - constant with float, str(ufloat) values
            "normalized.dg.json",
            {
                "at": {"indices": [1, 2, 3]},
                "constants": [
                    {"as": "mass", "value": 6.35, "units": "kg"},
                    {"as": "element", "value": 12},
                    {"as": "volume", "value": "5.546(0)", "units": "l"},
                ],
            },
            "constant.multiple.pkl",
        ),
        (  # ts9 - interpolate from datagram onto explicit timestamps
            "normalized.dg.json",
            {
                "at": {
                    "timestamps": [1575360000.0 + i * 200.0 for i in range(10)],
                    "step": "a",
                },
                "columns": [{"key": "derived->xin->O2", "as": "xin->O2"}],
            },
            "interpolated.at.single.pkl",
        ),
    ],
)
def test_extract_single(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    with open(inpath, "r") as infile:
        dg = json.load(infile)
    df = dgpost.utils.extract(dg, spec)
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)
    assert ref.attrs == df.attrs


@pytest.mark.parametrize(
    "inpath, spec, outpath",
    [
        (  # ts0 - interpolate explicit variable on one step
            "normalized.dg.json",
            [
                {
                    "at": {"step": "b1"},
                    "columns": [{"key": "derived->xout->O2", "as": "xout->O2"}],
                },
                {
                    "at": {"step": 0},
                    "columns": [{"key": "derived->xin->O2", "as": "xin->O2"}],
                },
            ],
            "interpolated.single.pkl",
        ),
        (  # ts1 - interpolate explicit variable onto multiple steps
            "normalized.dg.json",
            [
                {
                    "at": {"indices": [1, 2, 3]},
                    "columns": [{"key": "derived->xout->O2", "as": "xout->O2"}],
                },
                {
                    "at": {"step": "a"},
                    "columns": [{"key": "derived->xin->O2", "as": "xin->O2"}],
                },
            ],
            "interpolated.multiple.pkl",
        ),
        (  # ts2 - interpolate a dict using * onto multiple steps
            "normalized.dg.json",
            [
                {
                    "at": {"indices": [1, 2, 3]},
                    "columns": [{"key": "derived->xout->*", "as": "xout"}],
                },
                {
                    "at": {"step": "a"},
                    "columns": [{"key": "derived->xin->*", "as": "xin"}],
                },
            ],
            "interpolated.starred.pkl",
        ),
        (  # ts3 - constant with float, str(ufloat) values
            "normalized.dg.json",
            [
                {
                    "at": {"timestamps": [1575360000.0 + i * 200.0 for i in range(10)]},
                    "constants": [{"as": "volume", "value": "5.546(0)", "units": "l"}],
                },
                {
                    "at": {"step": "a"},
                    "columns": [{"key": "derived->xin->O2", "as": "xin->O2"}],
                },
            ],
            "interpolated.timestamps.pkl",
        ),
    ],
)
def test_extract_multiple(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    with open(inpath, "r") as infile:
        dg = json.load(infile)
    for si in range(len(spec)):
        if si == 0:
            ret = dgpost.utils.extract(dg, spec[si])
            df = ret
        else:
            ret = dgpost.utils.extract(dg, spec[si], ret.index)
            temp = pd.concat([df, ret], axis=1)
            temp.attrs = df.attrs
            temp.attrs["units"].update(ret.attrs["units"])
            df = temp
    ref = pd.read_pickle(outpath)
    pd.testing.assert_frame_equal(ref, df, check_like=True)
    assert ref.attrs == df.attrs


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (  # ts0 - extract single column
            "ndot.units.ufloat.df.pkl",
            {
                "columns": [{"key": "nin->C3H8", "as": "C3H8"}],
            },
            "table.direct.named.pkl",
        ),
        (  # ts1 - extract starred columns
            "ndot.units.ufloat.df.pkl",
            {
                "columns": [{"key": "nin->*", "as": "in"}],
            },
            "table.direct.starred.pkl",
        ),
        (  # ts2 - extract & interpolate on explicit timesteps
            "ndot.units.ufloat.df.pkl",
            {
                "at": {"timestamps": [0.9, 1.1]},
                "columns": [{"key": "nin->C3H8", "as": "C3H8"}],
            },
            "table.interpolated.named.pkl",
        ),
        (  # ts3 - extract & interpolate on explicit timesteps OOB
            "ndot.units.ufloat.df.pkl",
            {
                "at": {"timestamps": [2, 2.5, 3.0]},
                "columns": [{"key": "nin->*", "as": "in"}],
            },
            "table.interpolated.starred.pkl",
        ),
    ],
)
def test_extract_from_table(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    ret = dgpost.utils.extract(df, spec)
    ref = pd.read_pickle(outfile)
    pd.testing.assert_frame_equal(ret, ref, check_like=True)
    assert ret.attrs == ref.attrs
