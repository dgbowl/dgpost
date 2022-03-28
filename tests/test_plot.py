import os

import dgpost.utils
import numpy as np
import pandas as pd
import pytest
from PIL import Image, ImageChops


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


test_style_1 = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial"],
    "font.size": 22,
    "axes.linewidth": 1.1,
    "axes.labelpad": 4.0,
    "axes.xmargin": 0.1,
    "axes.ymargin": 0.1,
    "figure.subplot.hspace": 0,
    "figure.subplot.left": 0.11,
    "figure.subplot.right": 0.946,
    "figure.subplot.bottom": 0.156,
    "figure.subplot.top": 0.965,
    "xtick.major.size": 4,
    "xtick.minor.size": 2.5,
    "xtick.major.width": 1.1,
    "xtick.minor.width": 1.1,
    "xtick.major.pad": 5,
    "xtick.minor.visible": True,
    "xtick.direction": "in",
    "xtick.top": True,
    "ytick.major.size": 4,
    "ytick.minor.size": 2.5,
    "ytick.major.width": 1.1,
    "ytick.minor.width": 1.1,
    "ytick.major.pad": 5,
    "ytick.minor.visible": True,
    "ytick.direction": "in",
    "ytick.right": True,
    "lines.markersize": 10,
    "lines.markeredgewidth": 0.8,
}


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
            "style": test_style_1,
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
                    "rows": (0, 1),
                    "cols": (0, 1),
                    "xlim": (0, 15),
                    "ylabel": "ylabel line",
                    "methods": {
                        "tick_params": {
                            "top": True,
                            "right": True,
                            "labelbottom": False,
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
                    "rows": (1, 2),
                    "cols": (0, 1),
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
            "nrows": 2,
            # "sharex": True,
            "save": {"fname": "test.complex.png"},
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
                    "rows": (0, 1),
                    "cols": (0, 2),
                    "xlim": (0, 15),
                    "ylabel": "ylabel line",
                    "xlabel": "xlabel line",
                    "methods": {
                        "tick_params": {
                            "top": True,
                            "right": True,
                            "labelbottom": False,
                            "labeltop": True,
                        },
                        "xaxis.set_label_position": {
                            "position": 'top',},
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
                    "rows": (1, 2),
                    "cols": (0, 1),
                    "xlim": (0, 15),
                    "xlabel": "xlabel 1 ",
                    "ylabel": "ylabel scatter",
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
                    "rows": (1, 2),
                    "cols": (1, 2),
                    "xlim": (0, 15),
                    "xlabel": "xlabel 2",
                    "methods": {
                        "tick_params": {
                            "top": True,
                            "right": True,
                            "labelright": True,
                            "labelleft": False,
                        },
                    },
                },
            ],
            "nrows": 2,
            "ncols": 2,
            # "sharex": True,
            "save": {"fname": "test.split.png"},
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
