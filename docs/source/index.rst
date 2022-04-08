**dgpost**: Datagram postprocessing tools
=========================================

A set of datagram postprocessing tools, functions, visualisations and export scripts.

dgpost is a Python library aimed at reproducible postprocessing of time-resolved 
data. It provides functions to load data from `datagrams` and :class:`pd.DataFrames`,
automatic datapoint interpolation using unix timestamps, a library of transformation
functions which contains implementations of common calculations in chemistry, catalysis,
electrochemistry, etc., and functions to save and plot the calculated data.

In addition to the above, dgpost is fully unit- and uncertainty-aware, using the 
`pint <https://pint.readthedocs.io/en/stable/>`_ and 
`uncertainties <https://pythonhosted.org/uncertainties/>`_ packages.

.. toctree::
   :maxdepth: 3
   :caption: dgpost features
   :hidden:

   installation
   usage
   features
   version

.. toctree::
   :maxdepth: 1
   :caption: dgpost components
   :hidden:

   modules
