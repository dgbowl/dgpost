import strictyaml as sy
import os

load = sy.Map(
    {"as": sy.Str(), "path": sy.Str(), sy.Optional("check", default=True): sy.Bool()}
)

save = sy.Map(
    {
        "table": sy.Str(),
        "as": sy.Str(),
        sy.Optional("type"): sy.Enum(["pkl", "json", "csv", "xlsx"]),
        sy.Optional("sigma", default=True): sy.Bool(),
    }
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

constant = sy.Map({"value": sy.Any(), "as": sy.Str(), sy.Optional("units"): sy.Str()})

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

transform = sy.Map(
    {
        "table": sy.Str(),
        "with": sy.Str(),
        "using": sy.Seq(sy.Any()),
    }
)

schema = sy.Map(
    {
        sy.Optional("load"): sy.Seq(load),
        sy.Optional("extract"): sy.Seq(extract),
        sy.Optional("transform"): sy.Seq(transform),
        sy.Optional("save"): sy.Seq(save),
    }
)
