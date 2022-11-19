"""
**chromatography**: chromatographic trace postprocessing library
----------------------------------------------------------------
.. codeauthor:: 
    Peter Kraus

Includes functions to integrate a chromatographic trace.

.. rubric:: Functions

.. autosummary::



"""

import logging
import pint
import numpy as np
from uncertainties import unumpy as unp
from yadg.dgutils import ureg
from scipy.signal import savgol_filter, find_peaks
from dgpost.utils.helpers import separate_data, load_data

logger = logging.getLogger(__name__)






@load_data(
    ("time", "s", list),
    ("signal", None, list),
)
def integrate_trace(
    time: pint.Quantity,
    signal: pint.Quantity,
    species: dict[str, dict], 
    polyorder: int = 3,
    window: int = 7,
    prominence: float = 1e-4,
    threshold: float = 1.0,
    output: str = "trace",
) -> dict[str, float]:
    
    yvals, ysigs, yunit = separate_data(signal)

    # Smooth values first
    if polyorder is None and window is None:
        logger.debug("No smoothing.")
        ysmooth = yvals
    else:
        if polyorder > window:
            raise RuntimeError(
                f"Provided polyorder '{polyorder}' is smaller than the "
                f"smoothing window '{window}."
            )
        ysmooth = savgol_filter(yvals, window, polyorder)
    
    # Pick peaks
    peakmax, _ = find_peaks(ysmooth, prominence=prominence * yvals.max())
    #peakmin, _ = find_peaks(ysmooth * -1, prominence=prominence * yvals.max()) 
    # gradient: find peaks and inflection points
    grad = np.gradient(yvals)
    gm = 1 * abs(grad) > 1e-10
    gradzero = np.nonzero(np.diff(np.sign(grad * gm)))[0] + 1
    # second derivative: find peaks
    hess = np.gradient(grad)
    hm = 1 * abs(hess) > 1e-10
    hesszero = np.nonzero(np.diff(np.sign(hess * hm)))[0] + 1
    
    # Find peak edges
    allpeaks = []
    for pmax in peakmax:
        # find the index of the first inflection point after pmax
        for i, hz in enumerate(hesszero):
            if hz > pmax:
                hi = i
                break
        # right of peak:
        rmin = False
        rthr = False
        for xi in range(hesszero[hi], yvals.size):
            # find first minimum/maximum after pmax
            if xi in gradzero and not rmin:
                rmin = xi
            # find first inflection point with gradient below threshold 
            if xi in hesszero[hi:] and not rthr:
                if abs(grad[xi]) < threshold:
                    rthr = xi
            if rthr and rmin:
                break
        rlim = min(rthr if rthr else yvals.size, rmin if rmin else yvals.size)
        if rlim == yvals.size:
            logger.warning("Possible mismatch of peak end.")
            rlim -= 1
        # left of peak
        lmin = False
        lthr = False
        for xi in range(0, hesszero[hi - 1])[::-1]:
            if xi in gradzero and not lmin:
                lmin = xi
            if xi in hesszero[: hi - 1] and not lthr:
                if abs(grad[xi]) < threshold:
                    lthr = xi
            if lthr and lmin:
                break
        llim = max(lthr if lthr else 0, lmin if lmin else 0)
        if llim == 0:
            logger.warning("Possible mismatch of peak start.")
        allpeaks.append({"llim": llim, "rlim": rlim, "max": pmax})
    

    truepeaks = {}
    for name, limits in species.items():
        lim = {}
        lim["l"], lim["r"] = limits["l"], limits["r"]
        for k in {"l", "r"}:
            if isinstance(lim[k], float):
                lim[k] = ureg.Quantity(lim[k], time.u)
            elif isinstance(lim[k], str):
                lim[k] = ureg.Quantity(lim[k])
        print(f"{lim=}")
        for p in allpeaks:
            if time[p["max"]] > lim["l"] and time[p["max"]] < lim["r"]:
                truepeaks[name] = p
                break
    
    interpolants = []
    for p in allpeaks:
        if len(interpolants) == 0:
            interpolants.append([p["llim"], p["rlim"]])
        else:
            if interpolants[-1][1] == p["llim"]:
                interpolants[-1][1] = p["rlim"]
            else:
                interpolants.append([p["llim"], p["rlim"]])
    bn = yvals.copy()
    bs = ysigs.copy()
    for pair in interpolants:
        n = pair[1] - pair[0]
        interp = np.interp(range(n), [0, n], [bn[pair[0]], bn[pair[1]]])
        bn[pair[0] : pair[1]] = interp
        bs[pair[0] : pair[1]] = np.zeros(n)
    
    baseline = ureg.Quantity(unp.uarray(bn, bs), yunit)

    retval = {}
    for k, v in truepeaks.items():
        s = v["llim"]
        e = v["rlim"] + 1
        py = signal[s:e] - baseline[s:e]
        px = time[s:e]
        A = np.trapz(py, px)
        retval[f"{output}->area->{k}"] = A
        retval[f"{output}->height->{k}"] = py[v["max"] - s]

    return retval