"""
.. codeauthor::
    Peter Kraus

Includes functions to integrate a chromatographic trace, and post-process an integrated
trace using calibration.

.. rubric:: Functions

.. autosummary::

    integrate_trace
    apply_calibration


"""

import logging
import pint
import numpy as np
from uncertainties import unumpy as unp
from scipy.signal import savgol_filter, find_peaks
from dgpost.utils.helpers import separate_data, load_data, columns_to_smiles

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
    """
    Chromatographic trace integration.

    Function which integrates peaks found in the chromatographic trace, which is
    itself defined as a set of ``time, signal`` arrays. The procedure is as
    follows:

      #) The ``signal`` is smoothed the Savigny-Golay filter, via the
         :func:`scipy.signal.savgol_filter`. For this, the arguments ``polyorder``
         and ``window`` are used.
      #) Peak maxima are found using :func:`scipy.signal.find_peaks`. For this,
         the argument ``prominence`` is used, scaled by ``max(abs(signal))``.
      #) Peak edges of every found peak are determined. The peak ends are either
         determined from the nearest minima, or from the nearest inflection point
         at which the gradient is below the ``threshold``.
      #) Peak maxima are matched against known peaks, provided in the ``species``
         argument. The peak is considered matching a species when its maximum is
         between the left and right limits defined in ``species``.
      #) A baseline is constructed by interpolating by copying the ``signal`` data
         and interpolating between the ends of all matched peaks. If consecutive
         peaks are found, the interpolation spans the whole domain.
      #) The baseline is subtracted from the signal and the peak areas are
         integrated using the :func:`numpy.trapz` function.
      #) The peak height is taken from the original ``signal`` data.

    The format of the ``species`` specification, used for peak matching, is as follows:

    .. code-block:: yaml

        "{{ species_name }}" :
            l:  pint.Quantity
            r:  pint.Quantity

    with the keys ``"l"`` and ``"r"`` corresponding to the left and right limit for the
    maximum of the peak. The limits can be either :class:`pint.Quantity`, or :class:`str`
    with the same dimensionality as ``time``, or a :class:`float` in which case the units
    of ``time`` are assumed.


    Parameters
    ----------
    time
        A :class:`pint.Quantity` array object determining the X-axis of the trace.
        By default in seconds.

    signal
        A :class:`pint.Quantity` array object containing the Y-axis of the trace.
        By default dimensionless.

    species
        A :class:`dict[str, dict]`, where the keys are species names and the
        values define the left and right limits for matching the peak maximum.

    polyorder
        An :class:`int` defining the order of the polynomial for the Savigny-Golay
        filter. Defaults to 3. The ``polyorder`` must be less than ``window``.

    window
        An :class:`int` defining the smoothing window for the Savigny-Golay filter.
        Defaults to 7. Must be odd. The ``polyorder`` must be less than ``window``.

    prominence
        A :class:`float` used to calculate the prominence of the peaks in ``signal``
        by scaling the ``max(abs(signal))``. Used in the peak picking process.
        Defaults to 0.0001.

    threshold
        A :class:`float` used to find ends of peaks by comparing to the gradient
        of ``signal`` at the nearest inflection points.

    output
        A :class:`str` prefix for the output namespace. The results are collated in
        the ``f"{output}->area`` namespace for peak areas and ``f"{output}->height``
        namespace for peak height.

    Returns
    -------
    retvals: dict[str, dict[str, pint.Quantity]
        A dictionary containing the peak areas and peak heights of matched peaks
        stored in namespaced :class:`pint.Quantities`.
    """

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
    # peakmin, _ = find_peaks(ysmooth * -1, prominence=prominence * yvals.max())
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
            if xi in gradzero[:] and not rmin:
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
            if xi in gradzero[:] and not lmin:
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
                lim[k] = pint.Quantity(lim[k], time.u)
            elif isinstance(lim[k], str):
                lim[k] = pint.Quantity(lim[k])
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

    baseline = pint.Quantity(unp.uarray(bn, bs), yunit)

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


def _inverse(y, m=1.0, c=None):
    m = pint.Quantity(m)
    if c is None:
        return y / m
    else:
        c = pint.Quantity(c)
        return (y - c) / m


def _linear(x, m=1.0, c=None):
    m = pint.Quantity(m)
    if c is None:
        return m * x
    else:
        c = pint.Quantity(c)
        return m * x + c


@load_data(
    ("areas", None, dict),
)
def apply_calibration(
    areas: pint.Quantity,
    calibration: dict[str, dict],
    output: str = "x",
) -> dict[str, float]:
    """
    Apply calibration to an integrated chromatographic trace.

    Function which applies calibration information, provided in a :class:`dict`, to
    an integrated chromatographic trace. Elements in the calibration :class:`dict` are
    treated as chemicals, matched against the chromatographic data using SMILES.

    The format of the ``calibration`` is as follows:

    .. code-block:: yaml

        "{{ species_name }}" :
            function: Literal["inverse", "linear"]
            m:  float
            c:  Optional[float]

    Two calibration functions are provided. Either the output value ``x`` is calculated
    as $x = (A - c) / m$, i.e. an "inverse" relationship, or using $x = m \\times A + c$,
    a "linear" relationship. The offset $c$ is optional. Both $m$ and $c$ are internally
    converted to :class:`pint.Quantity`, therefore they can be specified with uncertainty,
    but have to be annotated by appropriate units to convert the units of the peak areas
    to the desired output.


    Parameters
    ----------
    areas
        A :class:`dict` containing a namespace of :class:`pint.Quantity` containing the
        integrated peak areas $A$, with their keys corresponding to chemicals.

    calibration
        A :class:`dict` containing the calibration information for processing the above
        peak ``areas`` into the resulting :class:`pint.Quantity`.

    output
        The :class:`str` prefix for the output namespace.

    """
    ret = {}
    smiles = columns_to_smiles(areas=areas, cal=calibration)
    for k, v in smiles.items():
        if len({"areas", "cal"}.intersection(v)) == 2:
            tag = f"{output}->{v['cal']}"
            cal = calibration[v["cal"]]
            A = areas[v["areas"]]
            if cal.get("function", "inverse") == "inverse":
                y = _inverse(A, m=cal.get("m", 1.0), c=cal.get("c", None))
            elif cal["function"] == "linear":
                y = _linear(A, m=cal.get("m", 1.0), c=cal.get("c", None))
            ret[tag] = y
    return ret
