**dgpost** installation
-----------------------
Released versions of dgpost are available on the Python Package Index |pypi|.
Those can be installed using ``pip``:

.. code:: bash

    pip install dgpost

.. note::

    With an optional argument ``--pre``, you can install the latest tagged & built
    development versions of dgpost.

You can test whether dgpost has been installed correctly by running either of:

    >>> dgpost --version
    dgpost version 2.0a4

    >>> dgpost
    usage: dgpost [-h] [--version] [-v] [-q] [--patch PATCH] infile
    dgpost: error: the following arguments are required: infile

.. warning::

    If, after installation on Windows into a ``conda`` environment, the above commands crash with::

        ImportError: DLL load failed while importing rdBase: The specified module could not be found.

    You might have to re-install the ``rdkit`` library from a compatible source, such as
    ``conda-forge``. Create a new environment, and install ``rdkit`` using:

    .. code:: bash

       conda create -n newEnvName python=3.9 rdkit -c conda-forge

    Then install dgpost using ``pip`` as shown above.

Installation from source
````````````````````````
To install dgpost from source on Github, |gh|, you first need to clone the repository
and then you can install the development version of the package using ``pip``:

.. code:: bash

    git clone git@github.com:dgbowl/dgpost.git
    cd dgpost
    pip install -e .[testing,docs]

The targets ``[testing]`` and ``[docs]`` in the above are optional, and will install
the required dependencies to run the test suite and build the documentation,
respectively.

.. |pypi| image:: https://badgen.net/pypi/v/dgpost/?icon=pypi
    :target: https://pypi.org/project/dgpost

.. |gh| image:: https://badgen.net/github/tag/dgbowl/dgpost/?icon=github
    :target: https://github.com/dgbowl/dgpost