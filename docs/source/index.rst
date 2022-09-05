**dgpost**: datagram post-processing toolkit
============================================
.. image:: https://badgen.net/badge/docs/dgbowl.github.io/grey?icon=firefox
   :target: https://dgbowl.github.io/dgpost
.. image:: https://badgen.net/pypi/v/dgpost/?icon=pypi
   :target: https://pypi.org/project/dgpost
.. image:: https://badgen.net/github/tag/dgbowl/dgpost/?icon=github
   :target: https://github.com/dgbowl/dgpost
.. image:: https://badgen.net/lgtm/grade/g/dgbowl/dgpost/python/?logo=lgtm
   :target: https://lgtm.com/projects/g/dgbowl/dgpost/context:python

A set of datagram postprocessing tools, functions, visualisations and export scripts.

dgpost is a Python library for reproducible postprocessing of time-resolved data. 
It provides functions to load data from `datagrams` and :class:`pd.DataFrames`,
automatic datapoint interpolation using unix timestamps, a library of transformation
functions with implementations of common calculations in chemistry, catalysis,
electrochemistry, etc., and convenience functions to save and plot the calculated data.

dgpost relies on the `dgpost-recipe` schema, defined in the 
:mod:`dgbowl_schemas.dgpost_recipe` module of that package. 

In addition to the above, dgpost is fully unit- and uncertainty-aware, using the 
`pint <https://pint.readthedocs.io/en/stable/>`_ and 
`uncertainties <https://pythonhosted.org/uncertainties/>`_ packages.

.. toctree::
   :maxdepth: 3
   :caption: dgpost user manual
   :hidden:

   installation
   usage
   features
   version

.. toctree::
   :maxdepth: 2
   :caption: dgpost function library
   :hidden:

   apidoc/dgpost.transform.catalysis
   apidoc/dgpost.transform.electrochemistry
   apidoc/dgpost.transform.impedance
   apidoc/dgpost.transform.rates
   apidoc/dgpost.transform.reflection
   apidoc/dgpost.transform.table

.. toctree::
   :maxdepth: 2
   :caption: dgpost utility library
   :hidden:

   apidoc/dgpost.utils.load
   apidoc/dgpost.utils.extract
   apidoc/dgpost.utils.transform
   apidoc/dgpost.utils.plot
   apidoc/dgpost.utils.save

.. toctree::
   :maxdepth: 1
   :caption: dgpost developer manual
   :hidden:

   contributing
   apidoc/dgpost
