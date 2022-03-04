import os

from matplotlib import pyplot as plt


def apply_plot_style(style):
    pass


def plt_axes(ax, table, axargs):
    lines = axargs.pop("lines", [])
    ax.set(**axargs)
    for line in lines:
        y = line.pop("y")
        y_data = table[y]

        x_data = table.get(x) if (x := line.get("x")) else range(len(y_data))

        ax.plot(x_data, y_data, **line)
    return


def plot(table, style, axes, show, save, **figargs):
    apply_plot_style(style)

    # check if amount of axes correspond to amount of spaces in grid
    spaces = figargs.get("nrows", 1) * figargs.get("ncols", 1)

    if spaces != len(axes):
        raise ValueError("Not enough axes for grid")

    fig, axs = plt.subplots(squeeze=False, **figargs)

    for i, ax in enumerate(axes):
        plt_axes(axs[i % 2, i // 2], table, ax)

    if show:
        fig.show()

    if not save:
        return

    fig.savefig(**save)
    return
