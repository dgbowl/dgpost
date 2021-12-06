import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json

from itertools import cycle

def plotly_color_map(names):
    # From https://stackoverflow.com/a/44727682
    plotly_colors = cycle(['#1f77b4',  # muted blue
                           '#ff7f0e',  # safety orange
                           '#2ca02c',  # cooked asparagus green
                           '#d62728',  # brick red
                           '#9467bd',  # muted purple
                           '#8c564b',  # chestnut brown
                           '#e377c2',  # raspberry yogurt pink
                           '#7f7f7f',  # middle gray
                           '#bcbd22',  # curry yellow-green
                           '#17becf'  # blue-teal
                           ])

    return dict(zip(names, plotly_colors))

with open(os.path.join("data", "dg", "datagram.json")) as infile:
    dg = json.load(infile)

# figure out how many plots
nplots = 0
ntraces = 0
for step in dg["data"]:
    if step["metadata"]["tag"] != "gc":
        continue
    for tstep in step["timesteps"]:
        ntraces += 1
        if len(tstep["raw"]["traces"]) > nplots:
            nplots = len(tstep["raw"]["traces"])


fig = make_subplots(rows = nplots, cols = 1, shared_xaxes = True, vertical_spacing = 0.02)

cm = plotly_color_map(range(ntraces))


for step in dg["data"]:
    if step["metadata"]["tag"] != "gc":
        continue
    ti = 0
    for tstep in step["timesteps"]:
        ri = 1
        for detname, detspec in tstep["raw"]["detectors"].items():
            tid = detspec["id"]
            trace = tstep["raw"]["traces"][tid]
            fig.add_trace(go.Scatter(x = [x[0] for x in trace["x"]], 
                                     y = [y[0] for y in trace["y"]],
                                     line = dict(color=cm[ti]),
                                     name = tstep["fn"],
                                     hoverinfo = "skip",
                                     legendgroup = str(ti),
                                     showlegend = True if ri == 1 else False),
                          row = tid + 1, col = 1)
            specdata = tstep["derived"]["peaks"][detspec["calname"]]
            for spec, data in specdata.items():
                pm = data["peak"]["max"]
                fig.add_trace(go.Scatter(x = [tstep["raw"]["traces"][ri-1]["x"][pm][0]],
                                         y = [tstep["raw"]["traces"][ri-1]["y"][pm][0]],
                                         marker=dict(color=cm[ti], size=8),
                                         legendgroup = str(ti),
                                         showlegend = False, name = spec),
                              row = tid + 1, col = 1)
            ri += 1
        ti += 1

fig.show()