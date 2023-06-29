"""
.. codeauthor::
    Peter Kraus

The function :func:`dgpost.utils.transform.transform` processes the below specification
in order to do data transformation on an extracted (or supplied) :class:`pd.DataFrame`.

.. _dgpost.recipe transform:
.. autopydantic_model:: dgbowl_schemas.dgpost.recipe.Transform

.. warning::

    The arguments passed to the transformation function in the ``transform.using``
    :class:`Sequence` have to be :class:`dict` with :class:`str`-type keys. The
    values will be coerced to appropriate types using the transform function
    decorator: :func:`dgpost.transform.helpers.load_data`.

"""
import pandas as pd
import importlib


def transform(table: pd.DataFrame, withstr: str, using: list[dict]) -> None:
    """"""
    split = withstr.split(".")
    modname = ".".join(split[:-1])
    funcname = split[-1]
    if modname.startswith("dgpost"):
        pass
    else:
        modname = f"dgpost.transform.{modname}"
    m = importlib.import_module(modname)
    func = getattr(m, funcname)
    for argset in using:
        table = func(table, **argset)
    return table
