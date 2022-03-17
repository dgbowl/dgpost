"""
``extract``: Data extraction and interpolation routine.

The function :func:`dgpost.utils.extract.extract` processes the below specification
in order to extract the required data from the supplied datagram.

.. code-block:: yaml

  extract:
    - from:      !!str          # datagram name from "load.as" 
      as:        !!str          # name of the extracted DataFrame
      at:                       # specifies timestamps to form index of the DataFrame
        step:       !!str
        index:      !!int
        steps:      [!!str, ...]
        indices:    [!!int, ...]
        timestamps: [!!float, ...]
      constant:                 # add a constant 'value' at 'at', save as 'as'
        - value: !!str
          as:    !!str
      direct:                   # extract 'key' from 'at', save as 'as'
        - key:   !!str
          as:    !!str
      interpolated:             # interpolate 'key' along 'keyat' to 'at', save as 'as'
        - key:   !!str
          keyat:
            step:        !!str
            index:       !!int
            steps:      [!!str, ...]
            indices:    [!!int, ...]
            timestamps: [!!float, ...]
          as:    !!str


.. note::
    The keys ``from`` and ``as`` are not processed by :func:`extract`, they should be 
    used by its caller to supply the requested ``datagram`` and assign the returned 
    :class:`pd.DataFrame` into the correct variable.

Handling of sparse data depends on the extraction format specified:

  - for ``direct`` keys, if the value is not present at any of the timesteps specified
    in ``at``, a :class:`NaN` is added instead
  - for ``interpolated`` keys, if a value is missing at any of the timesteps specified
    in ``keyat``, that timestep is masked and the interpolation is performed from 
    neighbouring points

Interpolation of :class:`uc.ufloat` is performed separately for the nominal and error
component.

Units are added into the ``attrs`` dictionary of the :class:`pd.DataFrame` on a 
per-column basis.

Data from multiple datagrams can be combined into one :class:`pd.DataFrame` using a
YAML such as the following example:

.. code-block:: yaml

    load:
      - as: norm
        path: normalized.dg.json
      - as: sparse
        path: sparse.dg.json
    extract:
      - as: df
        from: norm
        at:
        step: "a"
        direct:
          - key: raw->T_f
            as: rawT
      - as: df
        from: sparse
        at:
        step: "a"
        interpolated:
          - key: derived->xout->*
            as: xout
            keyat:
              steps: b1, b2, b3

In this example, the concatenation of the two tables is straightforward, as the 
indices of the tables (defined using `"step"`) are the same. If the indices differ,
the concatenation raises a warning, and the resulting table will contain `NaNs`.

.. code-author: Peter Kraus <peter.kraus@empa.ch>
"""

import numpy as np
import pandas as pd
import uncertainties as uc
from uncertainties import unumpy as unp
from uncertainties.core import str_to_number_with_uncert as tuple_fromstr
from typing import Union


def _get_steps(datagram: dict, at: dict) -> list[int]:
    spec = []
    if "step" in at:
        spec.append(at["step"])
    if "steps" in at:
        spec += at["steps"]
    if "index" in at:
        spec.append(at["index"])
    if "indices" in at:
        spec += at["indices"]
    for si in range(len(spec)):
        if isinstance(spec[si], int):
            assert spec[si] < len(datagram["steps"]), (
                f"extract: specified step index {spec[si]} is out of bounds "
                f"of the supplied datagtam with {len(datagram['steps'])} steps."
            )
        elif isinstance(spec[si], str):
            found = False
            for ssi in range(len(datagram["steps"])):
                if spec[si] == datagram["steps"][ssi]["metadata"]["tag"]:
                    spec[si] = ssi
                    found = True
                    break
            assert found, (
                f"extract: specified step tag '{spec[si]}' was not found "
                f"among tags in the supplied datagram."
            )
    return spec


def _get_key_recurse(data, keylist):
    key = keylist.pop(0)
    if len(keylist) == 0:
        if key == "*":
            keyset = set()
            for tstep in data:
                if len({"n", "s", "u"}.intersection(tstep.keys())) != 3:
                    for k in tstep.keys():
                        keyset.add(k)
            keys = []
            vals = []
            for key in keyset:
                # we need to check if there's a nested level
                nkeys, nvals = _get_key_recurse([i.get(key, {}) for i in data], ["*"])
                if len(nkeys) == 0:
                    keys.append(key)
                    vals.append([i.get(key, None) for i in data])
                else:
                    for nk, nv in zip(nkeys, nvals):
                        keys.append(f"{key}->{nk}")
                        vals.append(nv)
            return keys, vals
        else:
            return [None], [[i.get(key, None) for i in data]]
    else:
        return _get_key_recurse([i[key] for i in data], keylist)


def _get_key(datagram: dict, steps: list[int], keyspec: str) -> tuple:
    keyspec = keyspec.split("->")
    data = []
    for si in steps:
        for tstep in datagram["steps"][si]["data"]:
            data.append(tstep)
    return _get_key_recurse(data, keyspec)


def _get_ts(obj: Union[dict, pd.DataFrame], at: Union[dict, None]) -> np.ndarray:
    if isinstance(obj, dict):
        steps = _get_steps(obj, at)
        _, ts = _get_key(obj, steps, "uts")
        return np.ravel(ts)
    elif isinstance(obj, pd.DataFrame):
        return np.array(obj.index)
    else:
        raise ValueError(
            "Object passed to '_get_ts' is neither a datagram nor pd.DataFrame"
        )


def _get_constant(spec, ts):
    nts = ts.size
    colvals = []
    colnames = []
    colunits = []
    for el in spec:
        colnames.append(el["as"])
        colunits.append(el.get("units", ""))
        if isinstance(el["value"], str):
            val = uc.ufloat_fromstr(el["value"])
        elif isinstance(el["value"], (int, float)):
            val = uc.ufloat(el["value"], 0)
        colvals.append(np.ones(nts) * val)
    return colnames, colvals, colunits


def _get_direct_df(spec, df):
    colvals = []
    colnames = []
    colunits = []
    for el in spec:
        if el["key"] in df.columns:
            keys = [el["key"]]
        elif el["key"].endswith("*"):
            keys = []
            for k in df.columns:
                if k.startswith(el["key"][:-1]):
                    keys.append(k)
        for k in keys:

            if k == el["key"]:
                asname = el["as"]
            else:
                asname = el["as"] + "->" + k.split("->")[-1]
            colnames.append(asname)
            colvals.append(df[k])
            if k in df.attrs["units"]:
                colunits.append(df.attrs["units"][k])
            else:
                colunits.append("")
    return colnames, colvals, colunits


def _get_direct_dg(spec, datagram, at):
    colvals = []
    colnames = []
    colunits = []
    steps = _get_steps(datagram, at)
    for el in spec:
        keys, vals = _get_key(datagram, steps, el["key"])
        for kk, vv in zip(keys, vals):
            if kk is None:
                colnames.append(el["as"])
            else:
                colnames.append(f"{el['as']}->{kk}")
            uvals = []
            units = None
            for i in vv:
                if i is None:
                    uvals.append(float("NaN"))
                    continue
                elif isinstance(i, dict) and isinstance(i["n"], float):
                    uvals.append(uc.ufloat(i["n"], i["s"]))
                elif isinstance(i, dict) and isinstance(i["n"], list):
                    uvals.append(unp.uarray(i["n"], i["s"]))
                else:
                    raise ValueError
                if units is None:
                    units = i["u"]
                else:
                    assert i["u"] == units
            colvals.append(uvals)
            colunits.append("" if units in [None, "-"] else units)
    return colnames, colvals, colunits


def _get_direct(spec, obj, at):
    if isinstance(obj, dict):
        return _get_direct_dg(spec, obj, at)
    elif isinstance(obj, pd.DataFrame):
        return _get_direct_df(spec, obj)


def _get_interpolated_df(spec, df, ts):
    colnames, colvals, colunits = _get_direct_df(spec, df)
    colint = []
    for vals in colvals:
        noms = unp.nominal_values(vals)
        sigs = unp.std_devs(vals)
        mask = ~np.isnan(noms) & ~np.isnan(sigs)
        inoms = np.interp(ts, df.index[mask], noms[mask])
        isigs = np.interp(ts, df.index[mask], sigs[mask])
        colint.append(unp.uarray(inoms, isigs))
    return colnames, colint, colunits


def _get_interpolated_dg(spec, datagram, at, ts):
    colvals = []
    colnames = []
    colunits = []
    for el in spec:
        _steps = _get_steps(datagram, at)
        keys, vals = _get_key(datagram, _steps, el["key"])
        _ts = _get_ts(datagram, at)
        for kk, vv in zip(keys, vals):
            if kk is None:
                colnames.append(el["as"])
            else:
                colnames.append(f"{el['as']}->{kk}")
            unoms = []
            usigs = []
            masks = []
            units = None
            for i in vv:
                if i is None:
                    unoms.append(float("NaN"))
                    usigs.append(float("NaN"))
                    masks.append(False)
                    continue
                elif isinstance(i, dict) and isinstance(i["n"], float):
                    unoms.append(i["n"])
                    usigs.append(i["s"])
                    masks.append(True)
                elif isinstance(i, dict) and isinstance(i["n"], list):
                    raise ValueError(
                        "Interpolation of array variables is not yet supported"
                    )
                else:
                    raise ValueError
                if units is None:
                    units = i["u"]
                else:
                    assert i["u"] == units
            mts = np.array(_ts)
            mun = np.array(unoms)
            mus = np.array(usigs)
            inoms = np.interp(ts, mts[masks], mun[masks])
            isigs = np.interp(ts, mts[masks], mus[masks])
            colvals.append(unp.uarray(inoms, isigs))
            colunits.append("" if units in [None, "-"] else units)
    return colnames, colvals, colunits


def _get_interp(spec, obj, at, ts):
    if isinstance(obj, dict):
        return _get_interpolated_dg(spec, obj, at, ts)
    elif isinstance(obj, pd.DataFrame):
        return _get_interpolated_df(spec, obj, ts)


def extract(
    obj: Union[dict, pd.DataFrame, None], spec: dict, index: list = None
) -> pd.DataFrame:
    """
    Data extracting function.

    Given a loaded ``datagram`` and extraction ``spec``, this routine creates, extracts,
    or interpolates the specified columns into a single :class:`pd.DataFrame`, using the
    extracted or specified timestamps.

    Parameters
    ----------
    object
        The loaded datagram in :class:`dict` format or a table as :class:`pd.Dataframe`.

    spec
        The ``extract`` component of the job specification.

    Returns
    -------
    pd.DataFrame
        The requested tabulated data.

    """
    cns = cvs = cus = []
    at = spec.get("at", None)
    if at is not None and "timestamps" in at:
        ts = np.array(at.pop("timestamps"))
        interpolate = True
    elif index is not None:
        ts = index
        interpolate = True
    elif obj is not None:
        ts = _get_ts(obj, at)
        interpolate = False
    else:
        raise RuntimeError("Cannot deduce timestamps.")

    if "constant" in spec.keys():
        cns, cvs, cus = _get_constant(spec.pop("constant"), ts)
    elif interpolate and "columns" in spec:
        cns, cvs, cus = _get_interp(spec.pop("columns"), obj, spec.pop("at", None), ts)
    elif "columns" in spec:
        cns, cvs, cus = _get_direct(spec.pop("columns"), obj, spec.pop("at", None))

    df = pd.DataFrame(index=ts)
    df.attrs["units"] = {}
    for name, vals, unit in zip(cns, cvs, cus):
        df[name] = vals
        df.attrs["units"][name] = unit
    return df
