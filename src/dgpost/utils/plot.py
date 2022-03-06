import pandas as pd
from matplotlib import pyplot as plt, axes


def apply_plot_style(style: dict):
    pass


def plt_axes(ax: axes.Axes, table: pd.DataFrame, axargs: dict):
    lines = axargs.pop("lines", [])
    for method, arguments in axargs.pop("methods", {}).items():
        getattr(ax, method)(**arguments)
    ax.set(**axargs)
    for line in lines:
        y = line.pop("y")
        y_data = table[y]

        x_data = table.get(x) if (x := line.pop("x", None)) else y_data.index

        kind = line.pop("kind", "scatter")

        if kind == "line":
            ax.plot(x_data, y_data, **line)
        elif kind == "scatter":
            ax.scatter(x_data, y_data, **line)
        else:
            raise ValueError(f"This kind of plot is not supported: '{kind}'")
    return


def plot(
    table: pd.DataFrame, style: dict, ax_args: list[dict], save: dict, **figargs
):
    apply_plot_style(style)

    # check if amount of axes correspond to amount of spaces in grid
    spaces = figargs.get("nrows", 1) * figargs.get("ncols", 1)

    if spaces != len(ax_args):
        raise ValueError("Not enough axes for grid")

    fig, axs = plt.subplots(squeeze=False, **figargs)

    for i, ax in enumerate(ax_args):
        plt_axes(axs[i % 2, i // 2], table, ax)

    if not save:
        return

    fig.savefig(**save)
    return
