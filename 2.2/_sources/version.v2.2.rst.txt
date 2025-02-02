**dgpost**-v2.2
---------------

.. image:: https://img.shields.io/static/v1?label=dgpost&message=v2.2&color=blue&logo=github
    :target: https://github.com/dgbowl/dgpost/tree/2.2
.. image:: https://img.shields.io/static/v1?label=dgpost&message=v2.2&color=blue&logo=pypi
    :target: https://pypi.org/project/dgpost/2.2/
.. image:: https://img.shields.io/static/v1?label=release%20date&message=2025-02-02&color=red&logo=pypi

.. sectionauthor::
    Peter Kraus

Developed in the `ConCat lab <https://tu.berlin/en/concat>`_ at Technische Universität Berlin.

An update to ``dgpost-2.1``, including the following changes:

- Dropped support for ``python < 3.10``.
- Modified peak-picking in :mod:`~dgpost.transform.reflection` to use :func:`scipy.signal.find_peaks`.
- Removed version checking from :mod:`dgpost` and its dependency on :mod:`requests`.
- Implemented integration tests for compatibility with :mod:`yadg`.


.. codeauthor::
    Ueli Sauter,
    Peter Kraus