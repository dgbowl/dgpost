**dgpost** installation
-----------------------
Released versions of dgpost are available on the Python Package Index |pypi|.
Those can be installed using ``pip``:

.. code:: bash

    pip install --pre dgpost

.. note::

    With the optional argument ``--pre``, the latest tagged & built development 
    version will be installed. To install the latest release, the ``--pre`` argument
    may be omitted.

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