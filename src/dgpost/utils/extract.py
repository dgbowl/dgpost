"""
.. codeauthor::
    Peter Kraus

The function :func:`dgpost.utils.extract.extract` processes the below specification
in order to extract the required data from the supplied datagram.

.. _dgpost.recipe extract:
.. autopydantic_model:: dgbowl_schemas.dgpost.recipe.Extract

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
import datatree
import xarray as xr
import uncertainties as uc
import uncertainties.unumpy as unp
from typing import Union, Any, Optional
import logging
from functools import singledispatch

from dgpost.utils.helpers import (
    arrow_to_multiindex,
    keys_in_df,
    key_to_tuple,
    set_units,
    get_units,
)

logger = logging.getLogger(__name__)


def get_step(
    obj: Union[pd.DataFrame, datatree.DataTree, dict, None],
    at: Optional[dict] = None,
) -> Union[pd.DataFrame, datatree.DataTree, list[dict], None]:
    if obj is None:
        return None
    elif isinstance(obj, pd.DataFrame):
        return obj
    elif isinstance(obj, datatree.DataTree):
        if at is not None and "step" in at:
            return obj[at["step"]]
        elif at is not None and "steps" in at:
            ret = []
            for s in at["steps"]:
                ret.append(obj[s])
            return tuple(ret)
        else:
            return obj
    elif isinstance(obj, dict):
        steps = []
        if "step" in at:
            steps.append(at["step"])
        if "steps" in at:
            steps += at["steps"]
        if "index" in at:
            steps.append(at["index"])
        if "indices" in at:
            steps += at["indices"]
        ret = []
        for step in steps:
            if isinstance(step, int):
                assert step < len(obj["steps"]), (
                    f"extract: specified step index {step} is out of bounds "
                    f"of the supplied datagtam with {len(obj['steps'])} steps."
                )
                ret += obj["steps"][step]["data"]
            elif isinstance(step, str):
                found = False
                for dgstep in obj["steps"]:
                    if step == dgstep["metadata"]["tag"]:
                        ret += dgstep["data"]
                        found = True
                        break
                assert found, (
                    f"extract: specified step tag '{step}' was not found "
                    f"among tags in the supplied datagram."
                )
        return ret


def get_constant(spec: dict, ts: pd.Index):
    series = []
    for el in spec:
        logger.debug("adding constant as '%s'", el["as"])
        if isinstance(el["value"], str):
            val = uc.ufloat_fromstr(el["value"])
        elif isinstance(el["value"], (int, float)):
            val = uc.ufloat(el["value"], 0)
        name = key_to_tuple(el["as"])
        ret = pd.Series(data=np.ones(ts.size) * val, name=name)
        ret.attrs["units"] = el.get("units", None)
        series.append(ret)
    return series


def extract(
    obj: Union[dict, pd.DataFrame, datatree.DataTree, None],
    spec: dict,
    index: pd.Index = None,
) -> pd.DataFrame:
    """"""
    at = spec.get("at", None)
    steps = get_step(obj, at)

    if "columns" in spec:
        series = extract_obj(steps, spec["columns"])
    else:
        series = []

    if index is not None:
        ts = np.array(index)
    elif at is not None and "timestamps" in at:
        ts = pd.Index(at["timestamps"])
    elif len(series) > 0:
        ts = series[0].index
    elif isinstance(steps, list):
        ts = pd.Index([t["uts"] for t in steps])
    else:
        raise RuntimeError("could not figure out timesteps")

    if "constants" in spec:
        series += get_constant(spec["constants"], ts)

    df = pd.DataFrame(data=None, index=ts)
    df.attrs["units"] = dict()
    for sr in series:
        if sr.index.equals(ts):
            df[sr.name] = sr
        else:
            noms = unp.nominal_values(sr)
            sigs = unp.std_devs(sr)
            mask = ~np.isnan(noms) & ~np.isnan(sigs)
            if np.any(mask):
                inoms = np.interp(df.index, sr.index[mask], noms[mask])
                isigs = np.interp(df.index, sr.index[mask], sigs[mask])
            else:
                inoms = np.ones(df.index.size) * np.NaN
                isigs = np.ones(df.index.size) * np.NaN
            newsr = pd.Series(data=unp.uarray(inoms, isigs), name=sr.name, index=ts)
            df[sr.name] = newsr
        set_units(sr.name, sr.attrs.get("units", None), df)
    ret = arrow_to_multiindex(df)
    return ret


@singledispatch
def extract_obj(obj: Any, columns: list[dict]) -> list[pd.Series]:
    raise RuntimeError(
        "extract: attempted to extract from unknown object of type "
        f"'{type(obj)}'. Only 'pd.DataFrame', 'xr.Dataset', 'dt.DataTree' "
        "and 'list[dict]' are supported."
    )


@extract_obj.register(pd.DataFrame)
def _(obj: pd.DataFrame, columns: list[dict]) -> list[pd.Series]:
    df = arrow_to_multiindex(obj)
    series = []
    for el in columns:
        logger.debug("extracting '%s' from table", el["key"])
        keys = keys_in_df(el["key"], df)
        ktup = key_to_tuple(el["key"])
        atup = key_to_tuple(el.get("as", el["key"]))
        for k in keys:
            if ktup == k:
                asname = atup
            elif len(ktup) < len(k):
                rest = k[len(ktup) :]
                asname = tuple(list(atup) + list(rest))
            else:
                raise RuntimeError(f"could not use '{el['as']=}' with {k=}")
            ret = pd.Series(data=df[k], name=asname)
            ret.attrs["units"] = get_units(k, df)
            series.append(ret)
    return series


@extract_obj.register(datatree.DataTree)
def _(obj: datatree.DataTree, columns: list[dict]) -> list[pd.Series]:
    def get_key_recurse(dt, keys):
        key = keys.pop(0)
        if len(keys) == 0:
            if f"{key}_std_err" in dt:
                return (dt[key], dt[f"{key}_std_err"])
            else:
                return (dt[key], None)
        else:
            return get_key_recurse(dt[key], keys)

    index = None
    series = []
    for el in columns:
        logger.debug("extracting '%s' from table", el["key"])
        ktup = key_to_tuple(el["key"])
        atup = key_to_tuple(el.get("as", el["key"]))

        vals, sigs = get_key_recurse(obj, list(ktup))

        # Handle multi-dimensional data. If there's a string coordinate,
        # such as "species", we need to split the dataset into columns.
        # If all coordinates are numeric, such as "freq" etc, do nothing.
        if len(vals.coords.dims) > 1:
            assert "uts" in vals.coords.dims
            for coord in vals.coords.dims:
                if vals.coords.dtypes[coord].kind in {"O", "U"}:
                    splits = vals[coord].values
                    break
        else:
            coord = None
            splits = [None]

        # Figure out the axis index. If "uts" is a coordinate, use that.
        # If not, get the "uts" coordinate from the dataset.
        if "uts" in vals and index is None:
            index = vals.get_index("uts")
        elif index is None:
            search = list(ktup)[:-1] + ["uts"]
            index, _ = get_key_recurse(obj, search)

        for split in splits:
            name = list(atup)
            if sigs is None:
                if coord is None:
                    data = vals
                else:
                    data = vals.loc[{coord: split}]
                    name.append(split)
            else:
                if split is None:
                    data = unp.uarray(vals, sigs)
                else:
                    data = unp.uarray(
                        vals.loc[{coord: split}], sigs.loc[{coord: split}]
                    )
                    name.append(split)

            if index.shape == data.shape:
                ret = pd.Series(data=data, index=index, name=tuple(name))
            # correct Index: n-dim data.
            elif index.shape[0] == data.shape[0]:
                ret = pd.Series(data=list(data), index=index, name=tuple(name))
            # incorrect Index: need to tile to make n-dim data.
            elif data.ndim == 1:
                data = np.tile(data, (index.shape[0], 1))
                ret = pd.Series(data=list(data), index=index, name=tuple(name))
            ret.attrs["units"] = vals.attrs.get("units", None)
            series.append(ret)
    return series


@extract_obj.register(list)
def _(obj: list, columns: list[dict]) -> list[pd.Series]:
    def get_key_recurse(data, keylist):
        key = keylist.pop(0)
        if len(keylist) == 0:
            if key == "*":
                keyset = set()
                for tstep in data:
                    if len({"n", "s", "u"}.intersection(tstep)) != 3:
                        for k in tstep.keys():
                            keyset.add(k)
                keys = []
                vals = []
                for key in keyset:
                    # we need to check if there's a nested level
                    nkeys, nvals = get_key_recurse(
                        [i.get(key, {}) for i in data], ["*"]
                    )
                    if len(nkeys) == 0:
                        keys.append(key)
                        vals.append([i.get(key, None) for i in data])
                    else:
                        for nk, nv in zip(nkeys, nvals):
                            keys.append(f"{key}->{nk}")
                            vals.append(nv)
                return keys, vals
            else:
                ret = [i.get(key, None) for i in data]
                if any(
                    [
                        isinstance(i, dict)
                        and len({"n", "s", "u"}.intersection(i)) != 3
                        for i in ret
                    ]
                ):
                    return get_key_recurse([i.get(key, {}) for i in data], ["*"])
                else:
                    return [None], [ret]
        else:
            return get_key_recurse([i[key] for i in data], keylist)

    series = []
    uts = [ts["uts"] for ts in obj]
    for el in columns:
        logger.debug("extracting '%s' from datagram", el["key"])
        keyspec = el["key"].split("->")
        keys, vals = get_key_recurse(obj, keyspec)
        atup = key_to_tuple(el.get("as", el["key"]))
        for kk, vv in zip(keys, vals):
            if kk is None:
                name = atup
            else:
                name = tuple(list(atup) + kk.split("->"))

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
                elif isinstance(i, (int, str)):
                    uvals.append(i)
                elif isinstance(i, list) and all(
                    [isinstance(ii, (int, str)) for ii in i]
                ):
                    uvals.append(i)
                else:
                    raise ValueError(f"{i=} is of unknown {type(i)=}")
                if units is None and isinstance(i, dict):
                    units = i["u"]
            ret = pd.Series(data=uvals, index=uts, name=name)
            ret.attrs["units"] = None if units in [None, "-", " "] else units
            series.append(ret)
    return series


@extract_obj.register(tuple)
def _(obj: tuple, columns: list[dict]) -> list[pd.Series]:
    series = None
    for step in obj:
        ret = extract_obj(step, columns)
        if series is None:
            series = ret
        else:
            for si, s in enumerate(series):
                for r in ret:
                    if r.name == s.name:
                        break
                series[si] = pd.concat([s, r], axis="index")
                break
    return series
