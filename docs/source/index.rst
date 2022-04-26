**dgpost**: datagram post-processing toolkit
============================================

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
   :maxdepth: 1
   :caption: dgpost developer manual
   :hidden:

   contributing
   dgpost
