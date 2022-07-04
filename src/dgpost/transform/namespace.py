"""
**namespace**: utilities for combining namespaces
-------------------------------------------------

Provides a convenience function :func:`~dgpost.transform.namespace.combine` which
can be used to combine ``->`` separated namespaces of values or chemicals into a 
single namespace.

.. codeauthor:: 
    Peter Kraus


"""
import pint

from dgpost.transform.helpers import load_data
from .helpers import columns_to_smiles
from collections import defaultdict

@load_data(
    ("a", None, dict),
    ("b", None, dict),
)
def combine(
    a: dict[str, pint.Quantity],
    b: dict[str, pint.Quantity],
    conflicts: str = "sum",
    output: str = "c",
    chemicals: bool = False,
) -> dict[str, pint.Quantity]:
    """
    Combines two namespaces into one. Unit checks are performed, with the resulting
    units corresponding to the units in namespace ``a``. By default, the output 
    namespace is called ``"c"``. Optionally, the keys in each namespace can be treated
    as chemicals.
    
    Parameters
    ----------
    a
        Namespace ``a``.

    b
        Namespace ``b``.
    
    conflicts
        Name resolution scheme. Can be either ``"sum"`` where conflicts are summed,
        or ``"replace"``, where conflicting values in ``a`` are overwritten by ``b``.
    
    chemicals
        Treat keys within ``a`` and ``b`` as chemicals, and combine them accordingly.
        Default is ``False``.

    output
        Namespace of the returned dictionary. By default ``"c"``.

    """
    ret = {}
    u = a[next(iter(a))].u

    if chemicals:
        names = columns_to_smiles(a=a, b=b)
    else:
        names = defaultdict(dict)
        for k in a.keys():
            names[k].update({"a": k})
        for k in b.keys():
            names[k].update({"b": k})

    for k, v in names.items():
        if "a" in v and "b" in v:
            if conflicts == "sum":
                ret[v["a"]] = a[v["a"]] + b[v["b"]]
            elif conflicts == "replace":
                ret[v["a"]] = b[v["b"]].to(u)
            else:
                raise ValueError(f"Unknown value of 'conflicts': {conflicts}")
        elif "a" in v:
            ret[v["a"]] = a[v["a"]]
        elif "b" in v:
            ret[v["b"]] = b[v["b"]].to(u)
    
    out = {}
    for k, v in ret.items():
        out[f"{output}->{k}"] = v

    return out
