**dgpost** features
-------------------

.. note::

    For an overview of the data-processing features within dgpost, see the
    documentation of the :mod:`dgpost.transform` module.

`Pandas <https://pandas.pydata.org/>`_ compatibility
````````````````````````````````````````````````````
One of the design goals of dgpost was to develop a library that can be used with
:mod:`yadg` `datagrams`, the :class:`pd.DataFrames` created by dgpost, as well as with any
other :class:`pd.DataFrames`, created e.g. by parsing an ``xlsx`` or ``csv``
file.

This is achieved by placing some necessary requirements on the functions in the
:mod:`dgpost.transform` module. The key requirements are:

- the function must process :class:`pint.Quantity` objects,
- the function must return data in a :class:`dict[str, pint.Quantity]` format.

If these requirements are met, the decorator function
:func:`~dgpost.transform.helpers.load_data` can be used to either extract data
from the supplied :class:`pd.DataFrame`, or wrap directly supplied data into
:class:`pint.Quantity` objects, and supply those into the called ``transform``
function transparently to the user.

.. note::

    As of ``dgpost-2.0``, dgpost internally converts the loaded tables into
    :class:`pd.DataFrames` with :class:`pd.MultiIndex` as the column index, if
    necessary. All namespaces separated by ``->`` will be split into a
    :class:`pd.MultiIndex`, and the units of those columns will be organised
    accordingly. This means dgpost can read :class:`pd.MultiIndexed` tables, and
    extract data from tables with standard a :class:`pd.Index` as well as
    :class:`pd.MultiIndex` seamlessly.

Units and uncertainties
```````````````````````
Another key objective of dgpost is to allow and encourage annotating data by units
as well as error estimates / uncertainties. The design philosophy here is that by
building unit- and uncertainty- awareness into the toolchain, users will be encouraged
to use it, and in case of uncertainties, be more thoughtful about the limitations
of their data.

As discussed in the
`documentation of yadg <https://dgbowl.github.io/yadg/master/features.html>`_,
when experimental data is loaded from `datagrams`, it is annotated with units by
default. In dgpost, the units for the data in each column in each table are stored
as a :class:`dict[str, str]` in the ``"units"`` key of the  ``df.attrs`` attribute,
and they are extracted and exported appropriately when the table is saved.

If the ``df.attrs`` attribute does not contain the ``"units"`` entry, dgpost assumes
the underlying data is unitless, and the default units selected for each function in
the :mod:`dgpost.transform` library by its developers are applied to the data.
Internally, all units are handled using yadg's custom :class:`pint.UnitRegistry`,
via the `pint <https://pint.readthedocs.io/en/stable/>`_ library.

Uncertainties are handled using the linear uncertainty propagation library,
`uncertainties <https://pythonhosted.org/uncertainties/>`_. As the input data for
the functions in the :mod:`dgpost.transform` module is passed using
:class:`pint.Quantity` objects, which supports the :class:`uncetainties.unumpy`
arrays, uncertainty handling is generally transparent to both user and developer.
The notable exceptions here are transformations using fitting functions from the
`scipy <https://docs.scipy.org/doc/>`_ library, where arrays containing
:class:`floats` are expected - this has to be handled explicitly by the developer.

Uncertainty management, including stripping or setting uncertainties to user-provided
values, can be done on a per-column or per-namespace basis using the
:func:`~dgpost.transform.table.set_uncertainty` function from the :mod:`dgpost.transform.table`
module. Both absolute and relative errors can be supplied. The parser is fully
unit-aware.

When saving tables created in dgpost, the units are appended to the column names
(``csv/xlsx``) or stored in the table (``pkl/json``). When exporting a
:class:`pd.MultiIndexed` table to ``csv/xlsx``, units will be appended to the top-level
index. The uncertainties may be optionally dropped completely from the exported table;
see the :mod:`dgpost.utils.save` module. This is especially handy for post-processing of
tables in spreadsheets.

Provenance
``````````
Provenance tracking is implemented in dgpost using the ``"meta"`` entry of the
``df.attrs`` attribute of the created :class:`pd.DataFrame`. This entry is exported
when the :class:`pd.DataFrame` is saved as ``pkl/json``, and contains dgpost version
information as well as a copy of the `recipe` used to create the saved object.