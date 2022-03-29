**dgpost** features
-------------------

`Pandas <https://pandas.pydata.org/>`_ compatibility
````````````````````````````````````````````````````
One of the design goals of dgpost was to create a library that can be used with
`datagrams` and "custom" :class:`pd.DataFrames` created by dgpost, as well as with
"standard" :class:`pd.DataFrames` created e.g. by parsing an ``xlsx`` or ``csv``
file.

This is achieved by placing some necessary requirements on the functions in the 
:mod:`dgpost.transform` module (able to process :class:`pint.Quantity` objects,
returning data in a :class:`dict[str, pint.Quantity]` format), as well as by the
custom decorator function :func:`dgpost.transform.helpers.load_data` which handles
data extraction from :class:`pd.DataFrames` for the called ``transform`` function
transparently to the user.

Units and uncertainties
```````````````````````
Another key objective of dgpost is to allow and encourage annotating data by units
as well as error estimates / uncertainties. The design philosophy here is that by 
building unit- and uncertainty- awareness into the toolchain, its may be encouraged
to use it, and in case of uncertainties, be more thoughtful about the limitations
of their data.

As discussed in the `documentation of yadg <https://dgbowl.github.io/yadg/master/features.html>`_,
when experimental data is loaded from `datagrams`, it is annotated with units by
default. In dgpost, the units for the data in each column in each table are stored 
in the ``df.attrs["units"]`` :class:`dict[str, str]`, and they are exported 
appropriately when the table is saved. If the ``df.attrs`` attribute does not
contain the ``"units"`` entry, the underlying data is assumed to be unitless,
and the default units selected by the developers are applied to the data passed
into each function from the :mod:`dgpost.transform` module. Internally, all units
are handled using yadg's custom :class:`pint.UnitRegistry`, via the 
`pint <https://pint.readthedocs.io/en/stable/>`_ library.

Uncertainties are handled using the linear uncertainty propagation library,
`uncertainties <https://pythonhosted.org/uncertainties/>`_. As the input data for
the functions in the :mod:`dgpost.transform` module is passed using 
:class:`pint.Quantity` objects, which supports the :class:`uncetainties.unumpy`
arrays, uncertainty handling is generally transparent to both user and developer.
The notable exceptions here are transformations using fitting functions from the 
`scipy <https://docs.scipy.org/doc/>`_ library, where arrays containing 
:class:`floats` are expected - this has to be handled explicitly by the developer.

When saving tables created in dgpost, the units are appended to the column
names (``csv/xlsx``) or stored in the table (``pkl/json``), while the uncertainties
may be optionally dropped from the exported table.