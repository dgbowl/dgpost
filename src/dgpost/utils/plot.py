"""
``plot``: Plots columns of a DataFrame.

The function :func:`dgpost.utils.plot.plot` processes the below specification
in order to generate a plot:

.. code-block:: yaml

    plot:
      - table:      !!str       # internal DataFrame name
        style:      !!dict      # optional dictionary to adjust style of plot, see :class:`matplotlib.rcParams`
        fig_args:   !!dict      # optional kwargs for the generated :class:`matplotlib.figure.Figure`
        ax_args:                # sequence of arguments for the different axes
          cols:     !!tuple     # optional tuple (int, int) given the lower and upper bounds in the grid columns
          rows:     !!tuple     # optional tuple (int, int) given the lower and upper bounds in the grid rows
          series:               # sequence of different plot commands
            y:      !!str       # column label for y data
            x:      !!str       # optional column label for x data, or else index is used
            kind:   !!str       # optional kind of plot to produce, default `scatter'
                                # additional kwargs gets passed to plotting method
          methods:  !!dict      # optional kwargs where the key is an attribute of an :class:`matplotlib.axes.Axes`
                                # and the value is a dict containing kwargs to be called on the selected attribute
                                # also possible to call method on subobject of the `axes` i.e. `axes.xaxis.set_label_text`
        nrows:      !!int       # optional int defining the number of rows of the grid for :class:`matplotlib.gridspec.GridSpec`
        ncols:      !!int       # optional int defining the number of columns of the grid for :class:`matplotlib.gridspec.GridSpec`
        save:                   # optional to save the generated plot, `fname` required and any additional kwargs gets passed to :func:`matplotlib.figure.Figure.savefig`
          as:       !!str       # path, where the file is saved
          tight_layout: !!dict  # optional dictionary for figure.tight_figure

.. codeauthor:: Ueli Sauter
"""
import matplotlib
import pandas as pd
import uncertainties.unumpy as unp
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
        # datas processing
        # should I use here separate_data and pQ from dgpost.transform.helpers?
        # but with that I will lose the access to the index for x_data
        y = element.pop("y")
        y_data = table[y]
        y_values = unp.nominal_values(y_data.array)
        y_err = unp.std_devs(y_data.array)
        y_unit = table.attrs.get("units", {}).get(y, "")

        if x := element.pop("x", None):
            x_data = table[x]
            x_values = unp.nominal_values(x_data)
            x_err = unp.std_devs(x_data)
            x_unit = table.attrs.get("units", {}).get(x, "")
        else:
            x_values = y_data.index
            x_err = None
            x_unit = None

        kind = element.pop("kind", "scatter")

        if kind == "line":
            ax.plot(x_values, y_values, **element)
        elif kind == "scatter":
            ax.scatter(x_values, y_values, **element)
        elif kind == "errorbar":
            ax.errorbar(x_values, y_values, xerr=x_err, yerr=y_err, **element)
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
            gs[
                slice(*specs.pop("rows", (0, nrows))),
                slice(*specs.pop("cols", (0, ncols))),
            ]
        )
        plt_axes(ax, table, specs)

    if not save:
        return

    if save.get("tight_layout") is not None:
        fig.tight_layout(**save.pop("tight_layout"))
    fig.savefig(fname=save.pop("as"), **save)
    fig.show()
    return
