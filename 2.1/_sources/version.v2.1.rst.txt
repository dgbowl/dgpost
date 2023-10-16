**dgpost**-v2.1
---------------

.. image:: https://img.shields.io/static/v1?label=dgpost&message=v2.1&color=blue&logo=github
    :target: https://github.com/dgbowl/dgpost/tree/2.1
.. image:: https://img.shields.io/static/v1?label=dgpost&message=v2.1&color=blue&logo=pypi
    :target: https://pypi.org/project/dgpost/2.1/
.. image:: https://img.shields.io/static/v1?label=release%20date&message=2023-10-16&color=red&logo=pypi

.. sectionauthor::
    Peter Kraus

Developed in the `ConCat lab <https://tu.berlin/en/concat>`_ at Technische Universität Berlin.

An update to ``dgpost-2.0``, including the following features:

- :mod:`~dgpost.utils.load`: support for reading ``NetCDF`` files created by ``yadg-5.0``;
- :mod:`~dgpost.utils.pivot`: added a new functionality, allowing the users to reorganise
  data by grouping them into arrays from multiple rows;
- :mod:`~dgpost.utils.save`: added a new ``columns`` argument, allowing the user to select
  which columns of a table are to be exported;

.. codeauthor::
    Ueli Sauter,
    Peter Kraus