"""
**extract**: Data extraction and interpolation routine.
-------------------------------------------------------
.. codeauthor::
    Peter Kraus

The function :func:`dgpost.utils.extract.extract` processes the below specification
in order to extract the required data from the supplied datagram.

.. _dgpost.recipe extract:
.. autopydantic_model:: dgbowl_schemas.dgpost.recipe_1_1.extract.Extract

.. note::
    The keys ``from`` and ``into`` are not processed by :func:`extract`, they should 
    be used by its caller to supply the requested ``datagram`` and assign the returned 
    :class:`pd.DataFrame` into the correct variable.

Handling of sparse data depends on the extraction format specified:

  - for direct extraction, if the value is not present at any of the timesteps 
    specified in ``at``, a :class:`NaN` is added instead
  - for interpolation, if a value is missing at any of the timesteps specified
    in ``at`` or in the :class:`pd.DataFrame` index, that timestep is masked and 
    the interpolation is performed from neighbouring points

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
      - into: df
        from: norm
        at:
            step: "a"
        columns:
          - key: raw->T_f
            as: rawT
      - into: df
        from: sparse
        at:
            steps: b1, b2, b3
        direct:
          - key: derived->xout->*
            as: xout

In this example, the :class:`pd.DataFrame` is created with an index corresponding to
the timestamps of ``step: "a"`` of the datagram. The values specified using ``columns``
in the first section are entered directly, after renaming the column names.

The data pulled out of the datagram in the second step using the prescription in ``at``
are interpolated onto the index of the existing :class:`pd.DataFrame`.

"""
import numpy as np
import pandas as pd
import uncertainties as uc
import uncertainties.unumpy as unp
from typing import Union

from dgpost.transform.helpers import combine_tables


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
    nts = len(ts)
    colvals = []
    colnames = []
    colunits = []
    for el in spec:
        colnames.append(el["as"])
        colunits.append(el.get("units", None))
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
                colunits.append(None)
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
            colunits.append(None if units in [None, "-", " "] else units)
    return colnames, colvals, colunits


def _get_direct(spec, obj, at):
    if isinstance(obj, dict):
        return _get_direct_dg(spec, obj, at)
    elif isinstance(obj, pd.DataFrame):
        return _get_direct_df(spec, obj)


def _get_interp(spec, obj, at, ts):
    if isinstance(obj, dict):
        index = _get_ts(obj, at)
        colnames, colvals, colunits = _get_direct_dg(spec, obj, at)
    elif isinstance(obj, pd.DataFrame):
        index = obj.index
        colnames, colvals, colunits = _get_direct_df(spec, obj)
    colint = []
    for vals in colvals:
        noms = unp.nominal_values(vals)
        sigs = unp.std_devs(vals)
        mask = ~np.isnan(noms) & ~np.isnan(sigs)
        inoms = np.interp(ts, index[mask], noms[mask])
        isigs = np.interp(ts, index[mask], sigs[mask])
        colint.append(unp.uarray(inoms, isigs))
    return colnames, colint, colunits


def extract(
    obj: Union[dict, pd.DataFrame, None],
    spec: dict,
    index: list = None,
) -> pd.DataFrame:
    """"""
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

    if "constants" in spec.keys():
        cns, cvs, cus = _get_constant(spec.pop("constants"), ts)
    elif interpolate and "columns" in spec:
        cns, cvs, cus = _get_interp(spec.pop("columns"), obj, spec.pop("at", None), ts)
    elif "columns" in spec:
        cns, cvs, cus = _get_direct(spec.pop("columns"), obj, spec.pop("at", None))

    df = None
    units = {}
    for name, vals, unit in zip(cns, cvs, cus):
        if "->" in name:
            names = tuple(name.split("->"))
        else:
            names = name
        ddf = pd.DataFrame({names: pd.Series(vals, index = ts)})
        if df is None:
            df = ddf
        else:
            df = combine_tables(df, ddf)
        if unit is not None:
            units[names if isinstance(names, str) else "->".join(names)] = unit
    df.attrs["units"] = units
    return df