"""
``transform``: Reproducible transformations made simple

The function :func:`dgpost.utils.transform.transform` processes the below specification
in order to do data transformation on an extracted (or supplied) :class:`pd.DataFrame`.

.. code-block:: yaml

  transform:
    - table:            !!str  # name of the extracted DataFrame
      with:             !!str  # the transformation function name
      using:                   # the transformation function arguments
        - "{{ arg1 }}": !!str
          "{{ arg2 }}": !!str

.. warning::
    The arguments passed to the transformation function in the `transform.using` list
    have to be :class:`dict` with :class:`str`-type key-value pairs. It is the 
    responsiblity of the transformation function to coerce correct types!

"""
import pandas as pd
import importlib


def transform(table: pd.DataFrame, withstr: str, using: list[dict]) -> None:
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
        func(table, **argset)
