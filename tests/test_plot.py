import os

import dgpost.utils
import numpy as np
import pandas as pd
import pytest

from PIL import Image, ImageChops
from tests.utils import datadir


def are_images_equal(path_one, path_two):
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


@pytest.mark.parametrize(
    "input",
    [
        {
            "ax_args": [
                {
                    "lines": [
                        {
                            "y": "sin1",
                            "color": "r",
                            "label": "indices",
                            "kind": "line",
                        },
                        {
                            "y": "sin2",
                            "x": "ind",
                            "color": "b",
                            "label": "x_values",
                            "kind": "line",
                        },
                    ],
                    "xlim": (0, 15),
                    "xlabel": "xlabel",
                    "ylabel": "ylabel",
                },
            ],
            "style": "style",
            "save": {"fname": "test.trigo.png"},
        },
        {
            "ax_args": [
                {
                    "lines": [
                        {
                            "y": "sin1",
                            "color": "r",
                            "label": "indices",
                            "kind": "line",
                        },
                        {
                            "y": "sin2",
                            "x": "ind",
                            "color": "b",
                            "label": "x_values",
                            "kind": "line",
                        },
                    ],
                    "xlim": (0, 15),
                    "ylabel": "ylabel line",
                    "methods": {
                        "tick_params": {
                            "top": True,
                            "right": True,
                        },
                    },
                },
                {
                    "lines": [
                        {
                            "y": "sin1",
                            "color": "r",
                            "label": "indices",
                            "kind": "scatter",
                        },
                        {
                            "y": "sin2",
                            "x": "ind",
                            "color": "b",
                            "label": "x_values",
                            "kind": "scatter",
                        },
                    ],
                    "xlim": (0, 15),
                    "xlabel": "xlabel",
                    "ylabel": "ylabel scatter",
                    "methods": {
                        "tick_params": {
                            "top": True,
                            "right": True,
                            "labelright": True,
                        },
                    },
                },
            ],
            "style": "style",
            "nrows": 2,
            "sharex": True,
            "save": {"fname": "test.complex.png"},
        },
    ],
)
def test_plot(input, datadir):
    os.chdir(datadir)
    x_val = np.linspace(0, 6, 20)
    y_val = np.sin(x_val)
    input["table"] = pd.DataFrame({"ind": x_val, "sin1": y_val, "sin2": -y_val})
    dgpost.utils.plot(**input)
    img_name = input["save"]["fname"]
    are_images_equal(img_name, f"ref.{img_name}")
