import os
import dgpost.utils
import pandas as pd
import pytest
from .utils import compare_dfs


@pytest.mark.parametrize(
    "filetype",
    [
        # ts0 - save dataframe as pickle
        "pkl",
        # ts1 - save dataframe as json
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
        # ts4 - real-world dataframe
        "fe_gc.ufloat.df.pkl",
    ],
)
def test_save_vs_pkl(table, filetype, datadir):
    os.chdir(datadir)
    path = f"saved.{table.replace('pkl', filetype)}"
    refp = f"ref.{table}".replace(filetype, "pkl")
    dgpost.utils.save(table=pd.read_pickle(table), path=path, type=filetype)
    df = dgpost.utils.load(**{"path": path, "type": "table"})
    ref = dgpost.utils.load(**{"path": refp, "type": "table"})
    compare_dfs(ref, df, rtol=1e-5 if filetype == "pkl" else 2e-1)


@pytest.mark.parametrize(
    "filetype",
    [
        # ts0 - save dataframe as csv
        "csv",
        # ts1 - save dataframe as csv
        "xlsx",
    ],
)
@pytest.mark.parametrize(
    "table",
    [
        # ts0 - dataframe with float values
        "flowcx.float.df.pkl",
        # ts1 - dataframe with ufloat values
        "flowcx.ufloat.df.pkl",
        # ts2 - real-world dataframe
        "fe_gc.ufloat.df.pkl",
    ],
)
def test_save_vs_csv(table, filetype, datadir):
    os.chdir(datadir)
    path = f"saved.{table.replace('pkl', filetype)}"
    refp = f"ref.{table}".replace(filetype, "csv")
    dgpost.utils.save(table=pd.read_pickle(table), path=path, type=filetype)
    df = dgpost.utils.load(**{"path": table, "type": "table"})
    ref = dgpost.utils.load(**{"path": refp, "type": "table"})
    compare_dfs(ref, df)


def test_save_ordering(datadir):
    os.chdir(datadir)
    table = "fe_gc.ufloat.df.pkl"
    filetype = "xlsx"
    path = f"saved.{table.replace('pkl', filetype)}"
    refp = f"ref.{table.replace('pkl', filetype)}"
    dgpost.utils.save(table=pd.read_pickle(table), path=path, type=filetype)
    df = pd.read_excel(path)
    ref = pd.read_excel(refp)
    compare_dfs(ref, df, order=True)


@pytest.mark.parametrize(
    "columns, ncols",
    [
        (None, 57),
        (["I"], 1),
        (["fe(GC)"], 14),
        (["fe(GC)", "I"], 15),
    ],
)
def test_save_columns(columns, ncols, datadir):
    os.chdir(datadir)
    table = "fe_gc.ufloat.df.pkl"
    path = "test.pkl"
    dgpost.utils.save(table=pd.read_pickle(table), path=path, columns=columns)
    df = pd.read_pickle(path)
    print(df.head())
    assert len(df.columns) == ncols
