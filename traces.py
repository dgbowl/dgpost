import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import argparse
import logging
import json

import yadg.core
from yadg.core.validators import validate_schema

from cmap import plotly_color_map

def parse_arguments():
    parser = argparse.ArgumentParser(usage = """
        %(prog)s [options] schema
        """
    )
    parser.add_argument("schema",
                        help="File containing the schema to be processed by yadg"
                             " and plotted by traces.")
    parser.add_argument("--log", "--debug", "--loglevel", dest="debug",
                        help="Switch loglevel from WARNING to that provided.",
                        default="warning")
    args = parser.parse_args()
    if args.debug.upper() not in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]:
        parser.error(f"{args.debug.upper()} is not a valid loglevel.")
    else:
        logging.basicConfig(level = getattr(logging, args.debug.upper()))
    return args

def run():
    args = parse_arguments()
    assert os.path.exists(args.schema),f"traces: {args.schema} doesn't exist."
    logging.info("traces: opening schema")
    with open(args.schema) as infile:
        schema = json.load(infile)
    logging.info("traces: validating schema")
    validate_schema(schema)
    logging.info("traces: processing schema")
    dg = yadg.core.process_schema(schema)

    # figure out how many plots & traces
    nplots = 0
    ntraces = 0
    for step in dg["data"]:
        for tstep in step["timesteps"]:
            ntraces += 1
            if len(tstep["traces"]) > nplots:
                nplots = len(tstep["traces"])
    
    # make figure based on plots and get colormap
    fig = make_subplots(rows = nplots, cols = 1, shared_xaxes = True, vertical_spacing = 0.02)
    cm = plotly_color_map(range(ntraces))

    # lets plot each trace
    for step in dg["data"]:
        ti = 0
        for tstep in step["timesteps"]:
            ri = 1
            for detname, detspec in tstep["detectors"].items():
                tid = detspec["id"]
                trace = tstep["traces"][tid]
                fig.add_trace(go.Scatter(x = [x[0] for x in trace["x"]], 
                                         y = [y[0] for y in trace["y"]],
                                         line = dict(color=cm[ti]),
                                         name = tstep["fn"],
                                         hoverinfo = "skip",
                                         legendgroup = str(ti),
                                         showlegend = True if ri == 1 else False),
                              row = tid + 1, col = 1)
                specdata = tstep["peaks"][detspec["calname"]]
                for spec, data in specdata.items():
                    pm = data["peak"]["max"]
                    fig.add_trace(go.Scatter(x = [tstep["traces"][ri-1]["x"][pm][0]],
                                             y = [tstep["traces"][ri-1]["y"][pm][0]],
                                             marker=dict(color=cm[ti], size=8),
                                             legendgroup = str(ti),
                                             showlegend = False, name = spec),
                                  row = tid + 1, col = 1)
                ri += 1
            ti += 1
    fig.show()

if __name__ == "__main__":
    run()









