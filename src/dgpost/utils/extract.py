"""
``extract``: Data extraction and interpolation routine.

The function :func:`dgpost.utils.extract.extract` processes the below specification
in order do extract the required data from the supplied datagram.

.. code-block:: yaml

  extract:
    - from:      !!str          # datagram name from "load.as" 
      as:        !!str          # name of the extracted DataFrame
      at:                       # specifies timestamps to form index of the DataFrame
        step:       !!str
        index:      !int
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
    The keys ``from`` and ``as`` are not processed by :func:`dgpost.utils.extract.extract`, 
    they should be used by its caller to identify the requested ``datagram`` and assign 
    the returned :class:`pd.DataFrame` into the correct variable.

Handling of sparse data depends on the extraction format specified:

  - for ``direct`` keys, if the value is not present at any of the timesteps specified
    in ``at``, a :class:`NaN` is added instead
  - for ``interpolated`` keys, if a value is missing at any of the timesteps specified
    in ``keyat``, that timestep is masked and the interpolation is performed from 
    neighbouring points

Interpolation of :class:`uc.ufloat` is performed separately for the nominal and error
component.

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
        print(si)
        for tstep in datagram["steps"][si]["data"]:
            data.append(tstep)
    return _get_key_recurse(data, keyspec)


def _get_ts(datagram: dict, at: dict) -> np.ndarray:
    if "timestamps" in at:
        return np.array(at["timestamps"])
    else:
        steps = _get_steps(datagram, at)
        _, ts = _get_key(datagram, steps, "uts")
        return np.ravel(ts)


def _get_constant(spec, ts):
    nts = ts.size
    colvals = []
    colnames = []
    for el in spec:
        colnames.append(el["as"])
        if isinstance(el["value"], str):
            val = uc.ufloat_fromstr(el["value"])
        elif isinstance(el["value"], (int, float)):
            val = uc.ufloat(el["value"], 0)
        colvals.append(np.ones(nts) * val)
    return colnames, colvals


def _get_direct(spec, datagram, at):
    colvals = []
    colnames = []
    steps = _get_steps(datagram, at)
    for el in spec:
        keys, vals = _get_key(datagram, steps, el["key"])
        for kk, vv in zip(keys, vals):
            if kk is None:
                colnames.append(el["as"])
            else:
                colnames.append(f"{el['as']}->{kk}")
            uvals = []
            for i in vv:
                if i is None:
                    uvals.append(float("NaN"))
                elif isinstance(i, dict) and isinstance(i["n"], float):
                    uvals.append(uc.ufloat(i["n"], i["s"]))
                elif isinstance(i, dict) and isinstance(i["n"], list):
                    uvals.append(unp.uarray(i["n"], i["s"]))
                else:
                    raise ValueError
            colvals.append(uvals)
    return colnames, colvals


def _get_interpolated(spec, datagram, ts):
    colvals = []
    colnames = []
    for el in spec:
        _steps = _get_steps(datagram, el["keyat"])
        keys, vals = _get_key(datagram, _steps, el["key"])
        _ts = _get_ts(datagram, el["keyat"])
        for kk, vv in zip(keys, vals):
            if kk is None:
                colnames.append(el["as"])
            else:
                colnames.append(f"{el['as']}->{kk}")
            unoms = []
            usigs = []
            masks = []
            for i in vv:
                if i is None:
                    unoms.append(float("NaN"))
                    usigs.append(float("NaN"))
                    masks.append(1)
                elif isinstance(i, dict) and isinstance(i["n"], float):
                    unoms.append(i["n"])
                    usigs.append(i["s"])
                    masks.append(0)
                elif isinstance(i, dict) and isinstance(i["n"], list):
                    raise ValueError(
                        "Interpolation of array variables is not yet supported"
                    )
                else:
                    raise ValueError
            mts = np.ma.array(_ts, mask=masks)
            mun = np.ma.array(unoms, mask=masks)
            mus = np.ma.array(usigs, mask=masks)
            inoms = np.interp(ts, mts[mts.mask == False], mun[mun.mask == False])
            isigs = np.interp(ts, mts[mts.mask == False], mus[mus.mask == False])
            colvals.append(unp.uarray(inoms, isigs))
    return colnames, colvals


def extract(datagram: dict, spec: dict) -> pd.DataFrame:
    """
    Data extracting function.

    Given a loaded ``datagram`` and extraction ``spec``, this routine creates, extracts, 
    or interpolates the specified columns into a single :class:`pd.DataFrame`, using the
    extracted or specified timestamps.

    Parameters
    ----------
    datagram
        Loaded datagram in :class:`dict` format.

    spec
        The ``extract`` component of the job specification.
    
    Returns
    -------
    pd.DataFrame
        The requested tabulated data.

    """
    at = spec.pop("at")
    ts = _get_ts(datagram, at)
    colnames = []
    colvals = []
    if "constant" in spec.keys():
        cns, cvs = _get_constant(spec.pop("constant"), ts)
        colnames += cns
        colvals += cvs
    if "direct" in spec.keys():
        assert "timestamps" not in at, (
            "extract: cannot do a 'direct' extraction "
            "when 'at' contains arbitrary 'timestamps'"
        )
        cns, cvs = _get_direct(spec.pop("direct"), datagram, at)
        colnames += cns
        colvals += cvs
    if "interpolated" in spec.keys():
        cns, cvs = _get_interpolated(spec.pop("interpolated"), datagram, ts)
        colnames += cns
        colvals += cvs
    df = pd.DataFrame(index=ts)
    for name, vals in zip(colnames, colvals):
        df[name] = vals
    return df
