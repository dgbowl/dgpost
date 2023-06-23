import os
import dgpost.utils
from .utils import compare_dfs


def test_pivot_geis(datadir):
    os.chdir(datadir)
    plain = dgpost.utils.load("geis.plain.pkl", type="table")
    ret = dgpost.utils.pivot(
        table=plain,
        on="cycle number",
        columns=["freq", "real", "imag", "<Ewe>", "<I>"],
        timestamp="first",
    )
    ref = dgpost.utils.load("geis.trans.pkl", type="table")
    del ref.attrs["meta"]
    compare_dfs(ref, ret)
