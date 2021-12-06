"""
Data extraction, interpolation, and specification routines:



.. code-block:: yaml

  - constant:       Union[Ufloat, Tuple[float, float]]
  - direct:
      - key:        Dict[str]
  - interpolated:
      - step:
        tag:        Union[str, List[str]]
        index:      Union[int, List[int]]
      - key:        Dict[str]

.. code-block:: yaml

  - at:
      - points:     List[float]
      - step:       Union[str, List[str], int, List[int]]


Example:

.. code-block:: yaml
  
  - data:
    - at:
      - step:   "GC"
    - xout:
      - direct:
        - key:  "derived.xout.*"
    - xin:
      - interpolated:
        - key:  "derived.xin.*"
        - step: 0
  - transform:
    - Xp:
      - conversion:
        - xin:     "xin"
        - xout:    "xout"
        - feed:    "C3H8"
        - type:    "product"
        - element: "C"
    - Xr:
      - conversion:
        - xin:     "xin"
        - xout:    "xout"
        - feed:    "C3H8"
        - type:    "reactant"
        



"""

import numpy as np
import pandas as pd
import uncertainties as uc
from uncertainties import unumpy as unp
from typing import Union


def _steps(datagram: dict, at: dict) -> list[int]:
    if not isinstance(at["step"], list):
        steps = [at["step"]]
    else:
        steps = at["step"]
    for si in range(len(steps)):
        if isinstance(steps[si], int):
            assert steps[si] < len(datagram["steps"]), (
                f"extract: specified step index {steps[si]} is out of bounds "
                f"of the supplied datagtam with {len(datagram['steps'])} steps."
            )
        elif isinstance(steps[si], str):
            found = False
            for ssi in range(len(datagram["steps"])):
                if steps[si] == datagram["steps"][ssi]["metadata"]["tag"]:
                    steps[si] = ssi
                    found = True
                    break
            assert found, (
                f"extract: specified step tag '{steps[si]}' was not found "
                f"among tags in the supplied datagram."
            )
    return steps

def _get_key_recurse(data, keylist):
    key = keylist.pop(0)
    if len(keylist) == 0:
        if key == "*":
            keyset = set()
            for i in data:
                for k in i.keys():
                 keyset.add(k)
            keys = []
            vals = []
            for key in keyset:
                keys.append(key)
                vals.append([i.get(key, None) for i in data])
            return keys, vals
        else:
            return [None], [[i.get(key, None) for i in data]]
    else:
        return _get_key_recurse([i[key] for i in data], keylist)

def _get_key(datagram: dict, steps: list[int], keyspec: str) -> tuple:
    keyspec = keyspec.split("->")
    data = np.ravel([datagram["steps"][si]["data"] for si in steps])
    return _get_key_recurse(data, keyspec)


def _timestamps(datagram: dict, at: dict) -> list[float]:
    if "points" in at:
        return at["points"]
    elif "step" in at:
        steps = _steps(datagram, at)
        _, ts = _get_key(datagram, steps, "uts")
        return np.ravel(ts)

def extract(datagram: dict, spec: dict) -> np.ndarray:
    at = spec.pop("at")
    ts = _timestamps(datagram, at)
    colnames = []
    colvals = []
    for k, v in spec.items():
        if "direct" in v:
            key = v["direct"].pop("key")
            keys, vals = _get_key(datagram, _steps(datagram, at), key)
            for kk, vv in zip(keys, vals):
                if kk is None:
                    colnames.append(k)
                else:
                    colnames.append(f"{k}->{kk}")
                uvals = unp.uarray([i["n"] for i in vv], [i["s"] for i in vv])
                colvals.append(uvals)
        #elif "interpolated" in v:
        #    key = v["interpolated"].pop("key")
        #    sp = v["interpolated"]
        #    vals = _get_key(datagram, _steps(datagram, sp), key)
        #    unom = np.array([i["n"] for i in vals])
        #    usig = np.array([i["s"] for i in vals])
        #    stepts = _get_key(datagram, _steps(datagram, sp), "uts")
        #    inom = np.interp(ts, stepts, unom)
        #    isig = np.interp(ts, stepts, usig)
        #    colvals.append(unp.uarray(inom, isig))
    print(colnames, colvals, ts)
    return pd.DataFrame(np.asarray(colvals).T, index = ts, columns = colnames)
