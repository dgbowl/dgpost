import matplotlib
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec


def apply_plot_style(style: dict):
    if style is not None:
        matplotlib.rcParams.update(style)
    else:
        matplotlib.rcdefaults()


def plt_axes(ax: matplotlib.axes.Axes, table: pd.DataFrame, ax_args: dict):
    series = ax_args.pop("lines", [])
    for method, arguments in ax_args.pop("methods", {}).items():
        attr = ax
        for met in method.split("."):
            attr = getattr(attr, met)
        print(arguments)
        attr(**arguments)
    ax.set(**ax_args)
    for element in series:
        y = element.pop("y")
        y_data = table[y]

        x_data = table.get(x) if (x := element.pop("x", None)) else y_data.index

        kind = element.pop("kind", "scatter")

        if kind == "line":
            ax.plot(x_data, y_data, **element)
        elif kind == "scatter":
            ax.scatter(x_data, y_data, **element)
        else:
            raise ValueError(f"This kind of plot is not supported: '{kind}'")
    return


def plot(
    table: pd.DataFrame,
    ax_args: list[dict],
    save: dict,
    style: dict = None,
    fig_args: dict = None,
    **grid_args,
):
    apply_plot_style(style)

    grid_args["nrows"] = nrows = grid_args.get("nrows", 1)
    grid_args["ncols"] = ncols = grid_args.get("ncols", 1)

    gs = GridSpec(**grid_args)

    if fig_args is None:
        fig_args = {}

    fig = plt.figure(**fig_args)

    for specs in ax_args:
        ax = fig.add_subplot(
            gs[slice(*specs.pop("rows", (0, nrows))), slice(*specs.pop("cols", (0, ncols)))]
        )
        plt_axes(ax, table, specs)

    if not save:
        return

    fig.savefig(**save)
    fig.show()
    return
