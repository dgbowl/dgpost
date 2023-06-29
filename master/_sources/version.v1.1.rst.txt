**dgpost**-v1.1
---------------


.. image:: https://img.shields.io/static/v1?label=dgpost&message=v1.1&color=blue&logo=github
    :target: https://github.com/dgbowl/dgpost/tree/1.1
.. image:: https://img.shields.io/static/v1?label=dgpost&message=v1.1&color=blue&logo=pypi
    :target: https://pypi.org/project/dgpost/1.1/
.. image:: https://img.shields.io/static/v1?label=release%20date&message=2022-06-28&color=red&logo=pypi

.. sectionauthor::
    Peter Kraus

Developed in the Materials for Energy Conversion lab at Empa, in Dübendorf.

This is a bugfix release, including:

- ``--patch`` functionality, allowing the user to specify a file prefix on a command
  line when dgpost is executed;
- additional :mod:`~dgpost.transform.catalysis` functionality for calculating
  conversion using rates;
- fixes to index-based x-axes in single-column figures in the :mod:`~dgpost.utils.plot`
  module,
- support for the :mod:`~dgbowl_schemas.dgpost.recipe_1_1` schema.

.. codeauthor::
    Ueli Sauter,
    Peter Kraus