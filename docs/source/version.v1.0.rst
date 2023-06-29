**dgpost**-v1.0
---------------


.. image:: https://img.shields.io/static/v1?label=dgpost&message=v1.0&color=blue&logo=github
    :target: https://github.com/dgbowl/dgpost/tree/1.0
.. image:: https://img.shields.io/static/v1?label=dgpost&message=v1.0&color=blue&logo=pypi
    :target: https://pypi.org/project/dgpost/1.0/
.. image:: https://img.shields.io/static/v1?label=release%20date&message=2022-04-26&color=red&logo=pypi

.. sectionauthor::
    Peter Kraus

Developed in the Materials for Energy Conversion lab at Empa, in Dübendorf.

This initial release includes:

- :mod:`dgpost.utils` module, including an initial implementation of the
  :mod:`~dgpost.utils.load`, :mod:`~dgpost.utils.extract`,
  :mod:`~dgpost.utils.transform`, :mod:`~dgpost.utils.plot`, and
  :mod:`~dgpost.utils.save` functionalities,
- :mod:`dgpost.transform` module, including the
  :func:`~dgpost.transform.helpers.load_data` decorator and functions required
  to support the basic :mod:`~dgpost.utils.transform` functionality,
- several libraries within the :mod:`dgpost.transform` modules, including
  :mod:`~dgpost.transform.catalysis`, :mod:`~dgpost.transform.electrochemistry`,
  :mod:`~dgpost.transform.impedance`, and :mod:`~dgpost.transform.rates`,
- the :mod:`~dgbowl_schemas.dgpost.recipe_1_0` schema.

.. codeauthor::
    Ueli Sauter,
    Peter Kraus