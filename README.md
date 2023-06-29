# dgpost: datagram post-processing toolkit

[![Documentation](https://badgen.net/badge/docs/dgbowl.github.io/grey?icon=firefox)](https://dgbowl.github.io/dgpost)
[![PyPi version](https://badgen.net/pypi/v/dgpost/?icon=pypi)](https://pypi.org/project/dgpost)
![Github link](https://badgen.net/github/tag/dgbowl/dgpost/?icon=github)
![Github status](https://badgen.net/github/checks/dgbowl/dgpost/?icon=github)

Set of tools to post-process raw instrument data in **yadg**'s `datagram` format, ``NetCDF`` files, and tabulated data imported into `pd.DataFrames`.

### Capabilities:
**dgpost** is indended to be used as part of your data processing pipeline, and works best with a series of timestamped data.

Write a **Recipe** in `yaml`, and post-process your data from `NetCDF` files, `pd.DataFrames`, or `yadg.datagrams` in a reproducible fashion, while keeping provenance information, and without touching the original data files.

Post-process your data into pre-defined figures for your reports, or simply export your collated `pd.DataFrame` into one of the several supported formats!

Use **dgpost** in your Jupyter notebooks by importing it as a python package: `import dgpost.utils` to access the top-level functions for loading, extracting and exporting data; or `import dgpost.transform` to access the library of validated transform functions.

### Features:

**dgpost** can **load** data from multiple file formats, **extract** data from those files into `pd.DataFrames` and automatically interpolate the datapoints along the time-axis (generally the index of the `pd.DataFrame`) as necessary, **pivot** selected columns of the tables using another column as index, **transform** the created tables using functions from the built-in library, **plot** data from those tables using its matplotlib interface, and **save** the tables into several output formats.

Of course, **dgpost** is fully unit-aware, and supports values with uncertainties by using the `pint.Quantity` and `uncertainties.ufloat` under the hood.

For a further overview of features, see the [project documentation](https://dgbowl.github.io/dgpost).

### Contributors:
- [Peter Kraus](http://github.com/PeterKraus)
- [Ulrich Sauter](http://github.com/ileu)
