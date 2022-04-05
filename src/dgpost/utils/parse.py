"""
`parse`: YAML processing schema and loader/parser function.
"""
import os
import yaml
import json
from dgbowl_schemas.dgpost_recipe import recipe_parser 

    


def parse(fn: str) -> dict:
    """
    Input file parsing function.

    Currently, only yaml files are supported, hence this function is a wrapper around
    :func:`parse_yaml`.

    """
    assert os.path.exists(fn) and os.path.isfile(fn), (
        f"provided file name '{fn}' does not exist " f"or is not a valid file"
    )

    with open(fn, "r") as infile:
        if fn.endswith("yml") or fn.endswith("yaml"):
            indict = yaml.safe_load(infile)
        elif fn.endswith("json"):
            indict = json.load(infile)
    ret = recipe_parser(indict)    
    return ret

