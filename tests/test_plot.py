import os

import numpy as np
import pandas as pd
import pytest
import uncertainties.unumpy as unp
from PIL import Image, ImageChops

import dgpost.utils


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
    # "font.family": "sans-serif",
    # "font.sans-serif": ["Arial"],
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

x_val = np.linspace(0, 6, 20)
y_val = np.sin(x_val)
test_float_data = pd.DataFrame({"ind": x_val, "sin1": y_val, "sin2": -y_val})
test_ufloat_data = pd.DataFrame(
    {
        "ind": unp.uarray(x_val, 0.1),
        "sin1": unp.uarray(y_val, 0.1),
        "sin2": unp.uarray(-y_val, 0.1),
    }
)


@pytest.mark.parametrize(
    "input",
    [
        {  # ts0 - one image, lines, explicit labels, explicit colours, xlim
            "table": test_float_data,
            "ax_args": [
                {
                    "series": [
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
            "save": {"as": "test.trigo.png", "tight_layout": {}},
        },
        {  # ts1 - two images, lines & points, tickparams, xlabel: None
            "table": test_float_data,
            "ax_args": [
                {
                    "series": [
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
                    "xlabel": None,
                    "methods": {
                        "tick_params": {
                            "top": True,
                            "right": True,
                            "labelbottom": False,
                        },
                    },
                },
                {
                    "series": [
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
            "save": {"as": "test.complex.png", "tight_layout": {}},
        },
        {  # ts2 - three images, various sizes, label positions
            "table": test_float_data,
            "ax_args": [
                {
                    "series": [
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
                    "rows": (0, 2),
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
                        "xaxis.set_label_position": {"position": "top"},
                    },
                },
                {
                    "series": [
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
                    "rows": (2, 3),
                    "cols": (0, 1),
                    "xlim": (0, 15),
                    "xlabel": "xlabel 1 ",
                    "ylabel": "ylabel scatter left",
                    "methods": {
                        "tick_params": {
                            "top": True,
                            "right": True,
                        },
                    },
                },
                {
                    "series": [
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
                    "rows": (2, 3),
                    "cols": (1, 2),
                    "xlim": (0, 15),
                    "xlabel": "xlabel 2",
                    "ylabel": "ylabel scatter left",
                    "methods": {
                        "tick_params": {
                            "top": True,
                            "right": True,
                            "labelright": True,
                            "labelleft": False,
                        },
                        "yaxis.set_label_position": {
                            "position": "right",
                        },
                    },
                },
            ],
            "nrows": 3,
            "ncols": 2,
            "save": {"as": "test.split.png", "tight_layout": {}},
        },
        {  # ts3 - one image, errorbar, ls: "None"
            "table": test_ufloat_data,
            "ax_args": [
                {
                    "series": [
                        {
                            "y": "sin1",
                            "color": "r",
                            "label": "indices",
                            "kind": "errorbar",
                            "ls": "None",
                        },
                        {
                            "y": "sin2",
                            "x": "ind",
                            "color": "b",
                            "label": "x_values",
                            "kind": "errorbar",
                            "ls": "None",
                        },
                    ],
                    "xlim": (0, 15),
                    "xlabel": "xlabel",
                    "ylabel": "ylabel",
                },
            ],
            "style": test_style_1,
            "save": {"as": "test.errorbar.png", "tight_layout": {}},
        },
    ],
)
def test_plot_direct(input, datadir):
    os.chdir(datadir)
    img_name = input["save"]["as"]
    dgpost.utils.plot(**input)
    are_images_equal(img_name, f"ref.{img_name}")


@pytest.mark.parametrize(
    "data_file, input",
    [
        (  # ts0 - 3 images, composite data, legend, explicit latex labels
            "flowcx.units.ufloat.df.pkl",
            {
                "ax_args": [
                    {
                        "series": [
                            {
                                "y": "cin->*",
                                "colors": ["b", "r", "g"],
                                "kind": "scatter",
                            },
                        ],
                        "methods": {
                            "tick_params": {"labelbottom": False},
                        },
                        "rows": (0, 1),
                        "ylabel": "$C_{in}$",
                        "legend": True,
                    },
                    {
                        "series": [
                            {
                                "y": "xout->*",
                                "colors": ["b", "r", "g", "y", "brown"],
                                "kind": "scatter",
                            },
                        ],
                        "methods": {
                            "tick_params": {"labelbottom": False},
                        },
                        "rows": (1, 2),
                        "ylabel": "$X_{out}$",
                        "legend": True,
                    },
                    {
                        "series": [
                            {
                                "y": "flowin",
                                "color": "blue",
                                "kind": "line",
                            },
                            {
                                "y": "flowout",
                                "color": "red",
                                "kind": "line",
                            },
                        ],
                        "rows": (2, 3),
                        "xlabel": "index",
                        "ylabel": "$flow$",
                        "legend": True,
                    },
                ],
                "nrows": 3,
                "style": test_style_1,
                "fig_args": {
                    "figsize": (12, 12),
                },
                "save": {"as": "test.flowcx.withlabel.png", "tight_layout": {}},
            },
        ),
        (  # ts1 - 3 images, composite data, legend, implicit label & units
            "flowcx.units.ufloat.df.pkl",
            {
                "ax_args": [
                    {
                        "series": [
                            {
                                "y": "cin->*",
                                "colors": ["b", "r", "g"],
                                "kind": "scatter",
                            },
                        ],
                        "methods": {
                            "tick_params": {"labelbottom": False},
                        },
                        "rows": (0, 1),
                        "legend": True,
                    },
                    {
                        "series": [
                            {
                                "y": "xout->*",
                                "colors": ["b", "r", "g", "y", "brown"],
                                "kind": "scatter",
                            },
                        ],
                        "methods": {
                            "tick_params": {"labelbottom": False},
                        },
                        "rows": (1, 2),
                        "legend": True,
                    },
                    {
                        "series": [
                            {
                                "y": "flowin",
                                "color": "blue",
                                "kind": "line",
                            },
                            {
                                "y": "flowout",
                                "color": "red",
                                "kind": "line",
                            },
                        ],
                        "rows": (2, 3),
                        "legend": True,
                    },
                ],
                "nrows": 3,
                "style": test_style_1,
                "fig_args": {
                    "figsize": (12, 12),
                },
                "save": {"as": "test.flowcx.nolabel.png", "tight_layout": {}},
            },
        ),
    ],
)
def test_plot_from_df(data_file, input, datadir):
    os.chdir(datadir)
    img_name = input["save"]["as"]
    df = dgpost.utils.load(data_file, type="table")
    input["table"] = df
    dgpost.utils.plot(**input)
    are_images_equal(img_name, f"ref.{img_name}")
