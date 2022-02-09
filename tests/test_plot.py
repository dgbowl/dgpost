import os

import dgpost.utils
import numpy as np
import pandas as pd
import pytest

from tests.utils import datadir

@pytest.mark.parametrize(
    "input",
    [
        {
            "style": "style",
            "axes": [
                {
                    "lines": [
                        {
                            "y": "sin1",
                            "color": "r",
                        },
                        {
                            "y": "sin2",
                            "color": "b",
                        },
                    ],
                    "xlim": (0,7)
                },
            ],
            "show": True,
            "save": "",
        },
    ],
)
def test_plot(input, datadir):
    os.chdir(datadir)
    x_val = np.linspace(0, 6, 20)
    y_val = np.sin(x_val)
    input["table"] = pd.DataFrame({"ind": x_val, "sin1": y_val,"sin2": -y_val})
    dgpost.utils.plot(**input)
