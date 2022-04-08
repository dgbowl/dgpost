import pytest
import os
import json
import yadg.core
import pandas as pd
import numpy as np
import uncertainties.unumpy as unp
from PIL import Image, ImageChops
from typing import Sequence


def datagram_from_input(input, parser, datadir):
    schema = {
        "metadata": {
            "provenance": "manual",
            "schema_version": "0.1",
            "timezone": input.get("timezone", "UTC"),
        },
        "steps": [
            {
                "parser": parser,
                "import": {
                    "prefix": input.get("prefix", ""),
                    "suffix": input.get("suffix", ""),
                    "contains": input.get("contains", ""),
                    "encoding": input.get("encoding", "utf-8"),
                },
                "parameters": input.get("parameters", {}),
            }
        ],
    }
    if "case" in input:
        schema["steps"][0]["import"]["files"] = [input["case"]]
    elif "files" in input:
        schema["steps"][0]["import"]["files"] = input["files"]
    elif "folders" in input:
        schema["steps"][0]["import"]["folders"] = input["folders"]
    os.chdir(datadir)
    assert yadg.core.validators.validate_schema(schema)
    return yadg.core.process_schema(schema)


def standard_datagram_test(datagram, testspec):
    assert yadg.core.validators.validate_datagram(datagram), "datagram is invalid"
    assert len(datagram["steps"]) == testspec["nsteps"], "wrong number of steps"
    steps = datagram["steps"][testspec["step"]]["data"]
    assert len(steps) == testspec["nrows"], "wrong number of timesteps in a step"
    json.dumps(datagram)


def pars_datagram_test(datagram, testspec):
    steps = datagram["steps"][testspec["step"]]["data"]
    tstep = steps[testspec["point"]]
    for tk, tv in testspec["pars"].items():
        if tk != "uts":
            rd = "raw" if tv.get("raw", True) else "derived"
            assert (
                len(tstep[rd][tk].keys()) == 3
            ), "value not in [val, dev, unit] format"
            compare_result_dicts(
                tstep[rd][tk],
                {"n": tv["value"], "s": tv["sigma"], "u": tv["unit"]},
            )
        else:
            assert tstep[tk] == tv["value"], "wrong uts"


def compare_result_dicts(result, reference, atol=1e-6):
    assert result["n"] == pytest.approx(reference["n"], abs=atol)
    assert result["s"] == pytest.approx(reference["s"], abs=atol)
    assert result["u"] == reference["u"]


def compare_dfs(ref, df):
    pd.testing.assert_index_equal(ref.columns, df.columns, check_order=False)
    for col in ref.columns:
        r = ref[col].array
        t = df[col].array
        for ri, ti in zip(r, t):
            for func in {unp.nominal_values, unp.std_devs}:
                np.testing.assert_allclose(func(ri), func(ti))
    
    if "units" in ref.attrs or "units" in df.attrs:
        assert ref.attrs.get("units") == df.attrs.get("units")
    if "meta" in ref.attrs or "meta" in df.attrs:
        assert "provenance" in df.attrs["meta"]
        rrec = ref.attrs.get("meta", {}).get("recipe")
        drec = df.attrs.get("meta", {}).get("recipe")
        assert rrec == drec


def compare_images(path_one, path_two):
    """
    Compares two images with pillow
    see: https://stackoverflow.com/questions/35176639/compare-images-python-pil
    """
    img1 = Image.open(path_one)
    img2 = Image.open(path_two)

    equal_size = img1.height == img2.height and img1.width == img2.width
    assert equal_size

    if img1.mode == img2.mode == "RGBA":
        img1_alphas = [pixel[3] for pixel in img1.getdata()]
        img2_alphas = [pixel[3] for pixel in img2.getdata()]
        equal_alphas = img1_alphas == img2_alphas
    else:
        equal_alphas = True
    assert equal_alphas
    difference = ImageChops.difference(img1.convert("RGB"), img2.convert("RGB"))
    # difference.show()
    equal_content = not difference.getbbox()

    assert equal_content
