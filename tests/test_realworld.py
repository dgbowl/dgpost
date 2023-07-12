import pytest
import os
import pandas as pd
import dgpost

from .utils import compare_dfs, compare_images


@pytest.mark.parametrize(
    "inpath, reflist",
    [
        (  # ts0 - load 1 dg, extract 2 keys directly
            "ts0_empa",
            ["peis.pkl", "data.pkl", "transform.pkl", "plot.png"],
        ),
        (  # ts1 - load qftrace datagram, reflection prune, reflection qf
            "ts1_reflection",
            ["table.pkl"],
        ),
    ],
)
def test_realworld(inpath, reflist, datadir):
    os.chdir(datadir)
    os.chdir(inpath)
    flist = [fn for fn in sorted(os.listdir()) if fn.endswith("yaml")]
    assert len(flist) == len(reflist)
    for i, reffn in enumerate(reflist):
        dgpost.run(flist[i])
        if reffn.endswith("pkl"):
            ret = pd.read_pickle(reffn)
            print(f"{ret.columns=}")
            print(f"{ret.head()=}")
            ref = pd.read_pickle(f"ref.{reffn}")
            print(f"{ref.head()=}")
            ret.to_pickle(f"ref.{reffn}")
            compare_dfs(ref, ret)
        elif reffn.endswith("png"):
            compare_images(f"ref.{reffn}", reffn)
