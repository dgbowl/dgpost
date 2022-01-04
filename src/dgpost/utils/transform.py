"""
``transform``: Reproducible transformations made simple

The function :func:`dgpost.utils.transform.transform` processes the below specification
in order to do data transformation on an extracted (or supplied) :class:`pd.DataFrame`.

.. code-block:: yaml

  transform:
    - table:     !!str          # name of the extracted DataFrame
      with:      !!str          # the transformation function name
      using:     
"""
import pandas as pd
import importlib


def transform(table: pd.DataFrame, withstr: str, using: dict) -> None:
    split = withstr.split(".")
    modname = ".".join(split[:-1])
    funcname = split[-1]
    if modname.startswith("dgpost"):
        pass
    else:
        modname = f"dgpost.transform.{modname}"
    m = importlib.import_module(modname)
    func = getattr(m, funcname)
    func(table, **using)
