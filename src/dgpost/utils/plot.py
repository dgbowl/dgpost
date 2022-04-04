"""
``plot``: Plots columns of a DataFrame.

The function :func:`dgpost.utils.plot.plot` processes the below specification
in order to generate a plot:

.. code-block:: yaml

    plot:
      - table:               !!str   # internal DataFrame name
        style:               !!dict  # optional style dictionary for matplotlib.rcParams
        nrows:               !!int   # optional number of rows of matplotlib.gridspec.GridSpec
        ncols:               !!int   # optional number of columns of matplotlib.gridspec.GridSpec
        fig_args:            !!dict  # optional kwargs for the generated matplotlib.figure.Figure
        ax_args:                     # sequence of arguments for the different axes
          - cols:            !!tuple # optional (int, int) specifying grid columns for axes
            rows:            !!tuple # optional (int, int) specifying grid rows for axes
            series:                  # sequence of different plot commands
              - y:           !!str   # column label for y data
                x:           !!str   # optional column label for x data, or else index is used
                index:
                  from_zero: !!bool  # align values of index to zero
                  to_units:  !!str   # convert values of index to units of time
                kind:        !!str   # optional kind of plot to produce, default is scatter
                kwargs:      !!dict  # optional kwargs which are passed to the plotting method
            methods:         !!dict  # optional kwargs with methods of matplotlib.axes.Axes
                                     # and the value is a dict containing kwargs to be called 
                                     # on the selected attribute. Also possible to call 
                                     # method on subobject of the axes i.e. axes.xaxis.set_label_text
        save:                   
          as:                !!str   # file name where the plot is saved
          tight_layout:      !!dict  # optional dictionary for figure.tight_layout


.. codeauthor:: Ueli Sauter
"""
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import uncertainties.unumpy as unp


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
    series: list[dict] = ax_args.pop("series", [])

    for method, arguments in ax_args.pop("methods", {}).items():
        attr = ax
        # allows for method calls on attributes
        for met in method.split("."):
            attr = getattr(attr, met)
        attr(**arguments)

    for spec in series:
        kind = spec.pop("kind", "scatter")

        # data processing
        if (x := spec.pop("x", None)) is not None:
            x_data = table[x]
            x_values = unp.nominal_values(x_data)
            x_err = unp.std_devs(x_data)
            x_unit = table.attrs.get("units", {}).get(x, None)
        else:
            i_pars = {"from_zero": None, "to_units": None}
            i_pars.update(spec.pop("index", {}))
            x_err = None
            x_unit = None
            x_values = table.index
            if i_pars["from_zero"]:
                x = "time"
                x_values = x_values - x_values[0]
                if i_pars["to_units"] == "s" or max(x_values) < 120:
                    x_unit = "s"
                elif i_pars["to_units"] == "min" or max(x_values) < 7200:
                    x_unit = "min"
                    x_values = x_values / 60.0
                elif i_pars["to_units"] == "h" or max(x_values) >= 7200:
                    x_unit = "h"
                    x_values = x_values / 3600.0

        x_label = f"{x} [{x_unit}]" if x_unit is not None else x

        ys: list[dict] = []
        y = spec.pop("y")
        # check if multiple columns should be plotted
        if y.endswith("->*"):
            for col in sorted(table.columns):
                if y[:-1] in col:
                    ys.append(
                        {"k": col, "p": y.replace("->*", ""), "s": col.split("->")[-1]}
                    )
        else:
            ys.append({"k": y, "p": y, "s": y})

        for yi, yk in enumerate(ys):
            y_data = table[yk["k"]]
            y_values = unp.nominal_values(y_data.array)
            y_err = unp.std_devs(y_data.array)
            y_unit = table.attrs.get("units", {}).get(yk["k"], None)

            y_label = f"{yk['p']} [{y_unit}]" if y_unit is not None else yk["p"]
            kwargs = spec.copy()
            if "label" not in kwargs:
                kwargs["label"] = yk["s"]
            for k in list(kwargs):
                if k.endswith("s") and isinstance(kwargs[k], list):
                    klist = kwargs.pop(k)
                    kwargs[k[:-1]] = klist[yi % len(klist)]
            if kind == "line":
                ax.plot(x_values, y_values, **kwargs)
            elif kind == "scatter":
                ax.scatter(x_values, y_values, **kwargs)
            elif kind == "errorbar":
                ax.errorbar(x_values, y_values, xerr=x_err, yerr=y_err, **kwargs)
            else:
                raise ValueError(f"This kind of plot is not supported: '{kind}'")
        if x_unit is not None:
            ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
    ax.set(**ax_args)


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

    gs = gridspec.GridSpec(**grid_args)

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
        legend = specs.pop("legend", False)
        plt_axes(ax, table, specs)
        if legend:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    if not save:
        fig.show()
        return

    if save.get("tight_layout") is not None:
        fig.tight_layout(**save.pop("tight_layout"))
    else:
        fig.tight_layout()
    fig.savefig(fname=save.pop("as"), **save)
