import pytest
import os
import dgpost.utils
from .utils import compare_dfs


def test_pivot_geis(datadir):
    os.chdir(datadir)
    plain = dgpost.utils.load("geis.plain.pkl", type="table")
    ret = dgpost.utils.pivot(
        table=plain,
        using="cycle number",
        columns=["freq", "real", "imag", "<Ewe>", "<I>"],
        timestamp="first",
    )
    ref = dgpost.utils.load("geis.trans.pkl", type="table")
    compare_dfs(ref, ret, meta=False)


@pytest.mark.parametrize(
    "inpath",
    [
        "geis.transp.yml",
        "gcpl.transp.yml",
    ],
)
def test_pivot_run_yaml(inpath, datadir):
    os.chdir(datadir)
    dg, tab = dgpost.run(inpath)
    compare_dfs(tab["trans_a"], tab["trans_b"], meta=False)
