import os

import pandas as pd
import pytest
from dgpost.transform import permittivity
from .utils import compare_dfs


@pytest.mark.parametrize(
    "infile, spec, outfile",
    [
        (
            "data.Qf_T.pkl",
            [
                {
                    "f_mnp": "TM210->f0",
                    "temperature": "temperature->cavity",
                    "f_mnp_ref": "6528000000(10000) Hz",
                    "f_0n0_ref": "6461540000(10000) Hz",
                    "temperature_ref": "26.17(10) celsius",
                    "alpha_c": "23.000e-6 kelvin^(-1)",
                    "k_0n0": "25.838e-6 kelvin^(-1)",
                    "k_mnp": "9.275e-6 kelvin^(-1)",
                    "output": "ref->fe,p",
                },
            ],
            "ref.data.Qf_T.pkl",
        ),
    ],
)
def test_permittivity_ftT(infile, spec, outfile, datadir):
    os.chdir(datadir)
    df = pd.read_pickle(infile)
    for args in spec:
        df = permittivity.ftT_correction(df, **args)
    print(f"{df.head()=}")
    ref = pd.read_pickle(outfile)
    print(f"{ref.head()=}")
    df.to_pickle(outfile)
    compare_dfs(ref, df, meta=False)
