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

def extract(datagram: dict, at: dict, spec: dict) -> np.ndarray:
    