contributing to **dgpost**
==========================

Contributions are welcome! If you have a function or a module that you'd like to 
include in the :mod:`dgpost.transform` library, or a design suggestion for dgpost, 
please make a pull-request or an issue on `GitHub <https://github.com/dgbowl/dgpost>`_.

Developer documentation
```````````````````````
The project follows fairly standard developer practices. Every new feature should be 
implemented in a separate pull-request, and be associated with a unit test. Every pull-
request should be formatted using `black <https://black.readthedocs.io/en/stable/>`_ 
prior to merging.

Testing
```````
Tests are located in the ``tests`` folder of the repository, and are executed using
``pytest`` for every commit in every PR. 

The :mod:`tests.utils` module contains a convenience :class:`@pytest.fixture`, called 
:func:`~tests.utils.datadir`, which allows you to attach and load additional data 
(input files, schemas, etc.) as required by your test.

The :mod:`tests.utils` module also contains the :func:`~tests.utils.compare_dfs`
function, which should be used to compare :class:`pd.DataFrames`, as it handles 
comparison of tables including data with uncertainties, units, and the provenance 
information.

Documentation
`````````````
Each module within the :mod:`dgpost.transform` package should have a top-level 
docstring, including a short description of the functions in the module, and code
author names. 

Each function within the modules of the :mod:`dgpost.transform` library should be 
documented using a docstring within the function itself. Please document any non-
obvious maths as equations within the docstring.

