**dgpost**-v2.4
---------------

..
  .. image:: https://img.shields.io/static/v1?label=dgpost&message=v2.4&color=blue&logo=github
    :target: https://github.com/dgbowl/dgpost/tree/2.4
  .. image:: https://img.shields.io/static/v1?label=dgpost&message=v2.4&color=blue&logo=pypi
    :target: https://pypi.org/project/dgpost/2.4/
  .. image:: https://img.shields.io/static/v1?label=release%20date&message=2025-06-29&color=red&logo=pypi

.. sectionauthor::
    Peter Kraus

Developed in the `ConCat lab <https://tu.berlin/en/concat>`_ at Technische Universität Berlin.

.. warning::

    Minimum version of the :mod:`uncertainties` package has been increased to ``uncertainties>=3.2.0``. Pickle files created with previous versions of the :mod:`uncertainties` package may not be compatible.

An update to ``dgpost-2.3``, including the following changes:

- Added the :mod:`~dgpost.transform.permittivity` module for calculations related to complex permittivity and various corrections.
- Added a ``prominence`` parameter to pruning functions in :mod:`~dgpost.transform.reflection` module, allowing users a better control of peak picking using peak prominence.
- Removed the default ``height=0.2`` value used in :func:`~dgpost.transform.reflection.prune_cutoff` and :func:`~dgpost.transform.reflection.prune_gradient` functions
- Fixed more :obj:`np.nan` issues in the :mod:`~dgpost.transform.catalysis` module


.. codeauthor::
    Peter Kraus