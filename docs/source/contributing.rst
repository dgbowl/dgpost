contributing to **dgpost**
==========================

We are open to your contributions! If you have a function or a module that you'd
like to include in the :mod:`dgpost.transform` library, or a design suggestion,
please make a pull-request on GitHub.

Developer documentation
-----------------------

The project follows fairly standard developer practices. Every new feature should be
implemented in a pull-request, associated with a test, and every pull-request should 
be formatted using `black <https://black.readthedocs.io/en/stable/>`_ prior to merging.

Testing
```````
Tests are located in the ``tests`` folder of the repository, and are executed using
``pytest`` for every commit in every PR. 

The :mod:`tests.utils` module contains a convenience :class:`@pytest.fixture`, called 
:func:`~tests.utils.datadir`, which allows you to attach and load additional data 
(input files, schemas, etc.) as required by your test.

The :mod:`tests.utils` module also contains the :func:`~tests.utils.compare_dfs`, which
should be used to compare :class:`pd.DataFrames`, as it handles data with uncertainties,
units, and the provenance information.

Documentation
`````````````
Each module within the :mod:`dgpost.transform` package should have a top-level 
docstring, including a short description of the functions in the module, and code
author names. 

Each function within the modules of the :mod:`dgpost.transform` library should be 
documented using a docstring within the function itself. Please document any maths,

