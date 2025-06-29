**dgpost**-v2.3
---------------

.. image:: https://img.shields.io/static/v1?label=dgpost&message=v2.3&color=blue&logo=github
    :target: https://github.com/dgbowl/dgpost/tree/2.3
.. image:: https://img.shields.io/static/v1?label=dgpost&message=v2.3&color=blue&logo=pypi
    :target: https://pypi.org/project/dgpost/2.3/
.. image:: https://img.shields.io/static/v1?label=release%20date&message=2025-06-29&color=red&logo=pypi

.. sectionauthor::
    Peter Kraus

Developed in the `ConCat lab <https://tu.berlin/en/concat>`_ at Technische Universität Berlin.

An update to ``dgpost-2.2``, including the following changes:

- Added the :mod:`~dgpost.transform.complex` module for converting complex numbers between their polar and rectangular forms.
- Added the :mod:`~dgpost.transform.mixtures` module for converting between different representation of mixtures.
- Added the :func:`~dgpost.transform.table.apply_linear` and :func:`~dgpost.transform.table.apply_inverse` functions to allow application of calibrations or scaling factors to columns / namespaces.
- Added the :func:`~dgpost.transform.table.sum_namespace` function to provide a way to sum namespaces into a single column.
- Bug fixes to many division-by-zero bugs in the :mod:`~dgpost.transform.catalysis` module.
- Bug fix in :func:`~dgpost.transform.electrochemistry.fe` to count electrons properly when using charged species.


.. codeauthor::
    Ueli Sauter,
    Peter Kraus