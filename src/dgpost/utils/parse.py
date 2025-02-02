"""
**parse**: YAML and JSON input handler
--------------------------------------

.. codeauthor::
    Peter Kraus

"""

import os
import yaml
import json
from typing import Any, Union
from dgbowl_schemas.dgpost import to_recipe
import logging
from pydantic import BaseModel
from pydantic.v1 import BaseModel as BaseModel_v1
from packaging.version import Version

__latest_recipe__ = "2.1"
logger = logging.getLogger(__name__)


def update_recipe(object: Union[BaseModel, BaseModel_v1]) -> BaseModel:
    maxver = Version(__latest_recipe__)
    while hasattr(object, "update"):
        temp = object.update()
        if Version(temp.version) > maxver:
            break
        object = temp
    return object


def parse(fn: str) -> dict[str, Any]:
    """
    Input file parsing function.

    Supports loading ``yaml`` and ``json`` files using the `recipe`-parsing
    function and schema provided in the :mod:`dgbowl_schemas.dgpost.recipe`
    module.

    Parameters
    ----------
    fn
        Path to the filename to be parsed

    Returns
    -------
    ret: dict[str, Any]
        A dictionary representing the recipe.

    """
    assert os.path.exists(fn) and os.path.isfile(fn), (
        f"provided file name '{fn}' does not exist or is not a valid file"
    )

    logger.debug("loading recipe from '%s'" % fn)
    with open(fn, "r") as infile:
        if fn.endswith("yml") or fn.endswith("yaml"):
            indict = yaml.safe_load(infile)
        elif fn.endswith("json"):
            indict = json.load(infile)
    logger.debug("parsing loaded recipe dictionary")
    obj = update_recipe(to_recipe(**indict))
    ret = obj.model_dump(by_alias=True, exclude_none=True)
    return ret
