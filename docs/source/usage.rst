**dgpost** usage
----------------
dgpost is intended for use in two modes:

- with a recipe as an executable: ``dgpost <recipe.yml>``
- as a Python library: ``import dgpost.utils`` and ``import dgpost.transform``

These two usage modes are described below:

**dgpost** as an executable
```````````````````````````
This is the main user-focused way of using dgpost. The user should craft a 
`recipe`, written in ``yaml``, which includes a prescription of the steps to be
performed by dgpost. Currently supported steps are:

- :mod:`~dgpost.utils.load`: load a `datagram` or a :class:`pd.DataFrame`
- :mod:`~dgpost.utils.extract`: extract and interpolate data from the loaded files 
  into a table
- :mod:`~dgpost.utils.transform`: use a function from the :mod:`dgpost.transform` 
  library to process the data in the table, creating new columns
- :mod:`~dgpost.utils.plot`: plot parts of the table using our custom wrapper 
  around :mod:`matplotlib`
- :mod:`~dgpost.utils.save`: export the created table for further use

Each of the above keywords can be only specified once in the `recipe`, however more
than one command can be specified for each of the keywords (i.e. it's possible to 
:mod:`~dgpost.utils.load` multiple files, apply several ``transform`` functions, etc.). 
Detailed syntax of each of the above steps is further described in the documentation of 
each of the keywords within the :mod:`dgpost.utils` module.

dgpost can be used to process multiple datasets, in a batch-like mode, using the 
``--patch`` argument. For this, the `recipe` should contain either ``$patch`` or
``$PATCH`` in the :class:`str` defining the ``path`` in the :mod:`~dgpost.utils.load`
step. The same string can be included in the ``as`` argument of the :mod:`~dgpost.utils.save` 
and/or the ``save->as`` argument of the :mod:`~dgpost.utils.plot` steps. Then, dgpost 
can be executed using

.. code::

    dgpost --patch <patchname> <yamlfile>
  
and the paths in the provided ``yamlfile`` containing the `recipe` will be patched
using ``patchname``.

**dgpost** as a Python library
``````````````````````````````
For advanced users and more complex workflows, dgpost can be also imported as a
standard python library with ``import dgpost``. The functions within dgpost are
split into two key modules:

- :mod:`dgpost.utils` module, containing the ancilliary data management functions
  of dgpost, and
- :mod:`dgpost.transform` module, containing all "scientific" data transformation
  functions.

See the documentation of the two respective modules for details. The functionality
of dgpost can be used from within e.g. Jupyter notebooks in this way.