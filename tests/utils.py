import pytest
import pandas as pd
import numpy as np
import uncertainties.unumpy as unp
from PIL import Image, ImageChops
import datatree
import xarray as xr


def compare_result_dicts(result, reference, atol=1e-6):
    assert result["n"] == pytest.approx(reference["n"], abs=atol)
    assert result["s"] == pytest.approx(reference["s"], abs=atol)
    assert result["u"] == reference["u"]


def compare_dfs(ref, df, order=False, rtol=1e-5, meta=True):
    if "units" in ref.attrs or "units" in df.attrs:
        assert ref.attrs.get("units") == df.attrs.get("units")
    if meta and "meta" in ref.attrs or "meta" in df.attrs:
        assert "provenance" in df.attrs["meta"]
        rrec = ref.attrs.get("meta", {}).get("recipe")
        drec = df.attrs.get("meta", {}).get("recipe")
        assert rrec == drec
    pd.testing.assert_index_equal(ref.columns, df.columns, check_order=order)
    for col in ref.columns:
        r = ref[col].array
        t = df[col].array
        for ri, ti in zip(r, t):
            if isinstance(ri, (str, int)):
                assert ri == ti
            else:
                for func in {unp.nominal_values, unp.std_devs}:
                    assert np.allclose(func(ri), func(ti), equal_nan=True, rtol=rtol)


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


def compare_datatrees(ret: datatree.DataTree, ref: datatree.DataTree):
    for k in ret:
        assert k in ref, f"Entry {k} not present in reference DataTree."
    for k in ref:
        assert k in ret, f"Entry {k} not present in result DataTree."

    for k in ret:
        if isinstance(ret[k], datatree.DataTree):
            compare_datatrees(ret[k], ref[k])
        elif isinstance(ret[k], (xr.Dataset, xr.DataArray)):
            assert ret[k].to_dict() == ref[k].to_dict()
        else:
            raise RuntimeError(f"Unknown entry '{k}' of type '{type(k)}'.")
