"""
``plot``: Plots columns of a DataFrame.

The function :func:`dgpost.utils.plot.plot` processes the below specification
in order to generate a plot:

.. code-block:: yaml

    plot:
      - table:      !!str       # internal DataFrame name
        style:      !!dict      # optional dictionary to adjust style of plot, see :class:`matplotlib.rcParams`
        fig_args:   !!dict      # optional kwargs for the generated :class:`matplotlib.figure.Figure`
        save:                   # optional to save the generated plot, `fname` required and any additional kwargs gets passed to :func:`matplotlib.figure.Figure.savefig`
          fname:    !!str       # path, where the file is saved
        ax_args:                # sequence of arguments for the different axes
          series:               # sequence of different plot commands
            y:      !!str       # column label for y data
            x:      !!str       # optional column label for x data, or else index is used
            kind:   !!str       # optional kind of plot to produce, default `scatter'
                                # additional kwargs gets passed to plotting method
          legend:   !!dict      # TODO
          methods:  !!dict      # optional kwargs where the key is an attribute of an :class:`matplotlib.axes.Axes`
                                # and the value is a dict containing kwargs to be called on the selected attribute
                                # also possible to call method on subobject of the `axes` i.e. `axes.xaxis.set_label_text`

.. codeauthor:: Ueli Sauter
"""
import matplotlib
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec


def apply_plot_style(style: dict):
    """
    Updates the plot style with the given dictionary.
    For available kwargs see :class:`matplotlib.rcParams`.
    If style is None, applies/resets to the default matplotlib style.

    Parameters
    ----------
    style
        A dictionary object containing valid key/value pairs.

    """
    if style is not None:
        matplotlib.rcParams.update(style)
    else:
        matplotlib.rcdefaults()


def plt_axes(ax: matplotlib.axes.Axes, table: pd.DataFrame, ax_args: dict):
    """
    Processes ax_args and plots the data

    Parameters
    ----------
    ax
        axes to be plotted to
    table
        dataframe containing the data
    ax_args
        arguments for the axes

    """
    series = ax_args.pop("series", [])
    for method, arguments in ax_args.pop("methods", {}).items():
        attr = ax
        # allows for method calls on attributes
        for met in method.split("."):
            attr = getattr(attr, met)
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
