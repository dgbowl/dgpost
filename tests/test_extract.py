import pytest
import json
import os
import pandas as pd
import datatree

from dgpost.utils.helpers import combine_tables
import dgpost.utils
from .utils import compare_dfs


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
        (  # ts10 - extract integer values in a trace
            "ca+peis.datagram.json",
            {
                "at": {"step": "PEIS"},
                "columns": [
                    {"key": "raw->traces->PEIS->freq", "as": "freq"},
                    {"key": "raw->traces->PEIS->cycle number", "as": "cn"},
                ],
            },
            "ref.peis.single.pkl",
        ),
        (  # ts11 - extract integer and string values
            "ca+peis.datagram.json",
            {
                "at": {"step": "CA"},
                "columns": [
                    {"key": "raw->Ewe", "as": "Ewe"},
                    {"key": "raw->I Range", "as": "I Range"},
                    {"key": "raw->ox/red", "as": "ox/red"},
                ],
            },
            "ref.ca.single.pkl",
        ),
        (  # ts12 - sparse extract with arrow and implicit
            "sparse.dg.json",
            {
                "at": {"step": "a"},
                "columns": [
                    {"key": "derived->xin->*", "as": "a"},
                    {"key": "derived->xin", "as": "b"},
                ],
            },
            "ref.sparse.xin.pkl",
        ),
        (  # ts13 - extract single column
            "ndot.units.ufloat.df.pkl",
            {
                "columns": [{"key": "nin->C3H8", "as": "C3H8"}],
            },
            "table.direct.named.pkl",
        ),
        (  # ts14 - extract starred columns
            "ndot.units.ufloat.df.pkl",
            {
                "columns": [{"key": "nin->*", "as": "in"}],
            },
            "table.direct.starred.pkl",
        ),
        (  # ts15 - extract & interpolate on explicit timesteps
            "ndot.units.ufloat.df.pkl",
            {
                "at": {"timestamps": [0.9, 1.1]},
                "columns": [{"key": "nin->C3H8", "as": "C3H8"}],
            },
            "table.interpolated.named.pkl",
        ),
        (  # ts16 - extract & interpolate on explicit timesteps OOB
            "ndot.units.ufloat.df.pkl",
            {
                "at": {"timestamps": [2, 2.5, 3.0]},
                "columns": [{"key": "nin->*", "as": "in"}],
            },
            "table.interpolated.starred.pkl",
        ),
        (  # ts17 - extract 1D from NetCDF with at-step
            "meas+qf+gc.nc",
            {
                "at": {"step": "00-measurement.json"},
                "columns": [
                    {"key": "T_f", "as": "T"},
                ],
            },
            "ref.meas.pkl",
        ),
        (  # ts18 - extract 1D from NetCDF without at
            "meas+qf+gc.nc",
            {
                "columns": [
                    {"key": "00-measurement.json->T_f", "as": "T"},
                ],
            },
            "ref.meas.pkl",
        ),
        (  # ts19 - extract 1D from NetCDF with string coords
            "chromdata.nc",
            {
                "columns": [
                    {"key": "0->xout", "as": "xout"},
                    {"key": "0->concentration", "as": "c"},
                ],
            },
            "ref.chromdata.pkl",
        ),
        (  # ts20 - extract 1D from NetCDF with star
            "chromdata.nc",
            {
                "at": {"step": "0"},
                "columns": [
                    {"key": "xout->*", "as": "xout"},
                    {"key": "concentration->*", "as": "c"},
                ],
            },
            "ref.chromdata.pkl",
        ),
        (  # ts21 - extract 2D from NetCDF
            "qf+chrom.nc",
            {
                "at": {"step": "0/S11"},
                "columns": [
                    {"key": "freq", "as": "f"},
                    {"key": "Re(G)", "as": "real"},
                    {"key": "Im(G)", "as": "imag"},
                ],
            },
            "ref.qf.pkl",
        ),
        (  # ts22 - extract multiple steps from NetCDF
            "extract.steps.nc",
            {
                "at": {"steps": ["CA_02", "CV_01", "CV_02"]},
                "columns": [
                    {"key": "Ewe", "as": "Ewe"},
                    {"key": "<I>", "as": "I"},
                ],
            },
            "ref.ca+cv.pkl",
        ),
    ],
)
def test_extract_single(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    if inpath.endswith("json"):
        with open(inpath, "r") as inf:
            data = json.load(inf)
    elif inpath.endswith("pkl"):
        data = pd.read_pickle(inpath)
    elif inpath.endswith("nc"):
        data = datatree.open_datatree(inpath)
    ret = dgpost.utils.extract(data, spec)
    print(f"{ret.head()=}")
    ref = pd.read_pickle(outpath)
    print(f"{ref.head()=}")
    ret.to_pickle(outpath)
    compare_dfs(ref, ret)


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
        (  # ts3 - constant with float, str(ufloat) values
            "meas+qf+gc.nc",
            [
                {
                    "at": {"step": "01-inert.json/S11"},
                    "columns": [{"key": "freq"}, {"key": "Re(G)"}, {"key": "Re(G)"}],
                },
                {
                    "at": {"step": "00-measurement.json"},
                    "columns": [{"key": "T_f", "as": "temp"}],
                },
            ],
            "ref.qf+temp.pkl",
        ),
    ],
)
def test_extract_multiple(inpath, spec, outpath, datadir):
    os.chdir(datadir)
    if inpath.endswith("json"):
        with open(inpath, "r") as inf:
            data = json.load(inf)
    elif inpath.endswith("pkl"):
        data = pd.read_pickle(inpath)
    elif inpath.endswith("nc"):
        data = datatree.open_datatree(inpath)
    for si, sp in enumerate(spec):
        if si == 0:
            df = dgpost.utils.extract(data, sp)
        else:
            ret = dgpost.utils.extract(data, sp, df.index)
            df = combine_tables(df, ret)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outpath)
    print(f"{ref.head()=}")
    df.to_pickle(outpath)
    compare_dfs(ref, df)


@pytest.mark.parametrize(
    "inpath, outpath",
    [
        (  # ts0 - interpolate tables with nans
            "nan.yaml",
            "nan.df.pkl",
        ),
    ],
)
def test_extract_nan(inpath, outpath, datadir):
    os.chdir(datadir)
    dgpost.run(inpath)
    df = pd.read_pickle(outpath)
    print(f"{df.head()=}")
    ref = pd.read_pickle(f"ref.{outpath}")
    print(f"{ref.head()=}")
    df.to_pickle(f"ref.{outpath}")
    compare_dfs(ref, df)
