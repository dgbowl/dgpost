import strictyaml as sy

load = sy.Map(
    {
        "as": sy.Str(),
        "path": sy.Str(),
        sy.Optional("type", default="datagram"): sy.Enum(["datagram", "table"]),
        sy.Optional("check", default=True): sy.Bool(),
    }
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

column = sy.Map({"key": sy.Str(), "as": sy.Str()})


extract = sy.Map(
    {
        "into": sy.Str(),
        sy.Optional("from", default=None): sy.Str(),
        sy.Optional("at", default=None): at,
        sy.Optional("constant"): sy.Seq(constant),
        sy.Optional("columns"): sy.Seq(column),
    }
)

transform = sy.Map(
    {
        "table": sy.Str(),
        "with": sy.Str(),
        "using": sy.Seq(sy.Any()),
    }
)

lines = sy.MapCombined(
    {"y": sy.Str(), sy.Optional("x"): sy.Str()},
    sy.Str(),
    sy.Any(),
)

plot_legend = sy.MapCombined(
    {},
    sy.Str(),
    sy.Any(),
)

axes = sy.MapCombined(
    {
        "lines": sy.Seq(lines),
        "legend": plot_legend,
        sy.Optional("methods"): sy.MapPattern(sy.Str(), sy.Any())
    },
    sy.Str(),
    sy.Any(),
)

plot_save = sy.MapCombined(
    {
        "fname": sy.Str,
    },
    sy.Str(),
    sy.Any(),
)

plot = sy.MapCombined(
    {
        "style": sy.Str(),
        "table": sy.Str(),
        "ax_args": sy.Seq(axes),
        sy.Optional("save"): plot_save,
    },
    sy.Str(),
    sy.Any(),
)

schema = sy.Map(
    {
        sy.Optional("load"): sy.Seq(load),
        sy.Optional("extract"): sy.Seq(extract),
        sy.Optional("transform"): sy.Seq(transform),
        sy.Optional("save"): sy.Seq(save),
        sy.Optional("plot"): sy.Seq(plot),
    }
)
