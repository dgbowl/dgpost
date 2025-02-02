**dgpost**-v2.0
---------------

.. image:: https://img.shields.io/static/v1?label=dgpost&message=v2.0&color=blue&logo=github
    :target: https://github.com/dgbowl/dgpost/tree/2.0
.. image:: https://img.shields.io/static/v1?label=dgpost&message=v2.0&color=blue&logo=pypi
    :target: https://pypi.org/project/dgpost/2.0/
.. image:: https://img.shields.io/static/v1?label=release%20date&message=2023-01-13&color=red&logo=pypi

.. sectionauthor::
    Peter Kraus

Developed in the Materials for Energy Conversion lab at Empa, in Dübendorf, and
in the Centre for Advanced Ceramic Materials at the Technische Universität Berlin.

Second major release. Including all bug-fixes from the ``dgpost-1.x`` series, and
the following new features:

- support for :class:`pd.MultiIndex` in :class:`pd.DataFrames`;
- the :mod:`~dgpost.transform.table` module of functions for basic operations on tables;
- the :mod:`~dgpost.transform.chromatography` module, including functions for post-processing
  chromatographic traces;
- the :mod:`~dgpost.transform.reflection` module, containing utilities for post-processing
  reflection traces, including pruning and fitting functions.

.. codeauthor::
    Ueli Sauter,
    Peter Kraus