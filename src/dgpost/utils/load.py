"""
YAML processing schema and loader/parser function.
"""
import strictyaml as sy
import os

load = sy.Map(
    {"as": sy.Str(), "path": sy.Str(), sy.Optional("check", default=True): sy.Bool()}
)

at = sy.Map(
    {
        sy.Optional("step"): sy.Str(),
        sy.Optional("steps"): sy.CommaSeparated(sy.Str()),
        sy.Optional("index"): sy.Int(),
        sy.Optional("indices"): sy.CommaSeparated(sy.Int()),
        sy.Optional("timestamps"): sy.Seq(sy.Float()),
    }
)

constant = sy.Map({"value": sy.Any(), "as": sy.Str()})

direct = sy.Map({"key": sy.Str(), "as": sy.Str()})

interpolated = sy.Map({"key": sy.Str(), "as": sy.Str(), "keyat": at})

extract = sy.Map(
    {
        "as": sy.Str(),
        "from": sy.Str(),
        "at": at,
        sy.Optional("constant"): sy.Seq(constant),
        sy.Optional("direct"): sy.Seq(direct),
        sy.Optional("interpolated"): sy.Seq(interpolated),
    }
)

schema = sy.Map(
    {
        sy.Optional("load"): sy.Seq(load),
        sy.Optional("extract"): sy.Seq(extract),
    }
)


def load_yaml(fn: str) -> dict:
    """
    Loads the yaml file in ``fn``, parses it according to the schema, and returns
    the resulting specification dictionary.

    Parameters
    ----------
    fn
        Path to the yaml file to load.

    Returns
    -------
    dict
        The parsed job specification as a dictionary.

    """
    assert os.path.exists(fn) and os.path.isfile(fn), (
        f"load_yaml: provided file namen '{fn}' does not exist "
        f"or is not a valid file"
    )
    with open(fn, "r") as infile:
        yaml = infile.read()

    return sy.load(yaml, schema)
