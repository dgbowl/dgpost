"""
**reflection**: utilities for processing reflection coefficient traces
----------------------------------------------------------------------
.. codeauthor:: 
    Peter Kraus

Provides several functions for processing reflection coefficient traces. 

.. rubric:: Functions

.. autosummary::
   
    prune_cutoff
    prune_gradient


"""
from dgpost.utils.helpers import separate_data, load_data
import pint
from yadg.dgutils import ureg
import numpy as np
from scipy.signal import find_peaks
import uncertainties as uc


@load_data(
    ("real", None, list),
    ("imag", None, list),
    ("freq", "Hz", list),
)
def prune_cutoff(
    real: pint.Quantity,
    imag: pint.Quantity,
    freq: pint.Quantity,
    cutoff: float = 0.4,
    height: float = 1.0,
    distance: float = 5000.0,
    output: str = "pruned",
) -> dict[str, pint.Quantity]:
    """
    Cutoff-based reflection coefficient trace prune.

    Finds peak positions in :math:`\\text{abs}(\\Gamma)`, and then for each identified
    peak, prunes the trace around the peak maximum, using the cutoff as a fraction
    of the normalized peak height.

    Parameters
    ----------
    real
        A :class:`pint.Quantity` object containing the real part of the reflection
        coefficient data, :math:`\\text{Re}(\\Gamma)`. Unitless.

    imag
        A :class:`pint.Quantity` object containing the imaginary part of the reflection
        coefficient data, :math:`\\text{Im}(\\Gamma)`. Unitless.

    freq
        A :class:`pint.Quantity` object containing the frequencies :math:`f`
        corresponding to the reflection coefficient data. Defaults to ``Hz``.

    cutoff
        Relative peak height below which the trace is pruned Defaults to ``0.4``.

    height
        Peak finding height parameter. Defaults to ``1.0``.

    distance
        Peak finding distance parameter. Defaults to ``5000.0``.

    output
        Prefix for the output namespaces. If multiple peaks are found, the namespaces
        will be stored under  ``f"{output}({idx})"``, with ``freq``, ``imag`` and
        ``real`` as the columns within each namespace. Defaults to ``"pruned"``.

    Returns
    -------
    retvals: dict[str, pint.Quantity]
        A dictionary containing the pruned values of ``real``, ``imag`` and ``freq``
        data stored in namespaced :class:`pint.Quantities`.

    """
    re, _, _ = separate_data(real)
    im, _, _ = separate_data(imag)

    absgamma = np.abs(re + 1j * im)
    max_v = absgamma.max()
    peaks, _ = find_peaks(-10 * np.log10(absgamma), height=height, distance=distance)
    limits = []
    for pi in peaks:
        min_v = absgamma[pi]
        norm = absgamma - (min_v / (max_v / min_v))
        for l in range(pi - 1):
            li = pi - l
            if norm[li] <= cutoff:
                pass
            else:
                break
        for r in range(len(absgamma) - pi):
            ri = pi + r
            if norm[ri] <= cutoff:
                pass
            else:
                break
        limits.append((li + 1, ri - 1))
    ret = {}
    for pi, lim in enumerate(limits):
        tag = f"{output}({pi})" if len(limits) > 1 else output
        ret[f"{tag}->imag"] = imag[lim[0] : lim[1]]
        ret[f"{tag}->real"] = real[lim[0] : lim[1]]
        ret[f"{tag}->freq"] = freq[lim[0] : lim[1]]
    return ret


@load_data(
    ("real", None, list),
    ("imag", None, list),
    ("freq", "Hz", list),
)
def prune_gradient(
    real: pint.Quantity,
    imag: pint.Quantity,
    freq: pint.Quantity,
    threshold: float = 1e-6,
    height: float = 1.0,
    distance: float = 5000.0,
    output: str = "pruned",
) -> dict[str, pint.Quantity]:
    """
    Gradient-based prune.

    Finds peak positions in :math:`\\text{abs}(\\Gamma)`, and then for each identified
    peak, prunes the trace around the peak maximum, using the a threshold value in the
    gradient of :math:`\\text{abs}(\\Gamma)` as the criterium.

    Parameters
    ----------
    real
        A :class:`pint.Quantity` object containing the real part of the reflection
        coefficient data, :math:`\\text{Re}(\\Gamma)`. Unitless.

    imag
        A :class:`pint.Quantity` object containing the imaginary part of the reflection
        coefficient data, :math:`\\text{Im}(\\Gamma)`. Unitless.

    freq
        A :class:`pint.Quantity` object containing the frequencies :math:`f`
        corresponding to the reflection coefficient data. Defaults to ``Hz``.

    threshold
        Threshold for the gradient in the :math:`\\text{abs}(\\Gamma)` below which the
        trace is pruned. Defaults to ``1e-6``.

    height
        Peak finding height parameter. Defaults to ``1.0``.

    distance
        Peak finding distance parameter. Defaults to ``5000.0``.

    output
        Prefix for the output namespaces. If multiple peaks are found, the namespaces
        will be stored under  ``f"{output}({idx})"``, with ``freq``, ``imag`` and
        ``real`` as the columns within each namespace. Defaults to ``"pruned"``.

    Returns
    -------
    retvals: dict[str, pint.Quantity]
        A dictionary containing the pruned values of ``real``, ``imag`` and ``freq``
        data stored in namespaced :class:`pint.Quantities`.

    """

    re, _, _ = separate_data(real)
    im, _, _ = separate_data(imag)

    absgamma = np.abs(re + 1j * im)
    grad = np.gradient(absgamma)
    peaks, _ = find_peaks(-10 * np.log10(absgamma), height=height, distance=distance)
    limits = []

    for pi in peaks:
        for l in range(pi - 1):
            li = pi - l
            if abs(grad[li]) > threshold or l < 100:
                pass
            else:
                break
        for r in range(absgamma.size - pi):
            ri = pi + r
            if abs(grad[ri]) > threshold or r < 100:
                pass
            else:
                break
        limits.append((li + 1, ri - 1))
    ret = {}
    for pi, lim in enumerate(limits):
        tag = f"{output}({pi})" if len(limits) > 1 else output
        ret[f"{tag}->imag"] = imag[lim[0] : lim[1]]
        ret[f"{tag}->real"] = real[lim[0] : lim[1]]
        ret[f"{tag}->freq"] = freq[lim[0] : lim[1]]
    return ret


@load_data(
    ("real", None, list),
    ("imag", None, list),
    ("freq", "Hz", list),
)
def fit_kajfez(
    real: pint.Quantity,
    imag: pint.Quantity,
    freq: pint.Quantity,
    iterations: int = 5,
    output: str = None,
) -> dict[str, pint.Quantity]:
    """
    Kajfez's circle-fitting program.

    Adapted from Q0REFL.m, which is a part of Kajfez, D.: "Linear fractional curve
    fitting for measurement of high Q factors", IEEE Trans. Microwave Theory Techn.
    42 (1994) 1149-1153.

    This fitting process attempts to fit a circle to a near-circular section of
    points on a Smith's chart. It's robust, quick, and reliable, and produces
    reasonable error estimates.

    Parameters
    ----------
    fvals
        Nominal values of the frequencies
    fsigs
        Error values of the frequencies
    gvals
        Complex reflection coefficient values, :math:`\\Gamma(f)`.
    absgvals
        Absolute values of the reflection coefficient, :math:`|\\Gamma(f)|`

    Returns
    -------
    (Q0, f0): tuple[uc.ufloat, uc.ufloat]
        Fitted quality factor and central frequency of the data.
    """
    fren, fres, freu = separate_data(freq)
    im, _, _ = separate_data(imag)
    re, _, _ = separate_data(real)
    n = fren.size
    gam1 = re + 1j * im
    agam1 = np.abs(gam1)
    # dia = agam1.min()
    idia = np.argmax(agam1)
    f0 = fren[idia]
    ena = np.ones(n)
    sig = np.ones(3)
    # eps = np.ones(n)
    # p = np.zeros(n)
    for ite in range(iterations):
        x = 2 * (fren / f0 - ena)
        e3 = gam1 * x
        e2 = -ena
        e1 = -x
        F = -gam1
        x2 = abs(x) ** 2
        ga2 = abs(gam1) ** 2
        if ite == 0:
            p = 1.0 / (x2 * (ena + ga2) + ena)
        else:
            p = sig[1] ** 2 / (
                x2 * sig[0] ** 2 + sig[1] ** 2 + (x2 * ga2) * sig[2] ** 2
            )
        E = np.array([e1, e2, e3]).T
        PE = np.array([p * e1, p * e2, p * e3]).T
        C = E.conj().T @ PE  # @?
        q1 = E.conj().T @ (p * F)  # @ ?
        D = np.linalg.inv(C)
        g = D @ q1
        eps = g[0] * e1 + g[1] * e2 + g[2] * e3 - F
        S1sq = eps.conj().T @ (p * eps)
        # Fsq = F.conj().T @ (p * F)
        sumden = C[0, 0] * D[0, 0] + C[1, 1] * D[1, 1] + C[2, 2] * D[2, 2]
        for m in range(3):
            sig[m] = np.sqrt(abs(D[m, m] * S1sq / sumden))
        # diam1 = 2 * abs(g[1] * g[2] - g[0]) / abs(g[2].conj() - g[2])
        gamc1 = (g[2].conj() * g[1] - g[0]) / (g[2].conj() - g[2])
        gamd1 = g[0] / g[2]
        gam1L2 = 2 * gamc1 - gamd1
        delt = (g[1] - gam1L2) / (gam1L2 * g[2] - g[0])
        f0 = f0 * (1 + 0.5 * delt.real)
    f011 = f0
    dia1 = 2 * abs(g[1] * g[2] - g[0]) / abs(g[2].conj() - g[2])
    # flin = np.linspace(fre[0], fre[-1], 201)
    # ft = 2 * (flin / f011 - 1)
    # gam1com = (g[0] * ft.T + g[1]) / (g[2] * ft.T + 1)
    gam1d = g[0] / g[2]
    gam1c = (g[2].conj() * g[1] - g[0]) / (g[2].conj() - g[2])
    QL1 = g[2].imag

    # QL1 -> Q01
    ang1 = -np.arctan2((-gam1d).imag, (-gam1d).real)
    ang2 = np.arctan2((gam1c - gam1d).imag, (gam1c - gam1d).real)
    angtot = ang1 + ang2
    cob = np.cos(angtot)
    rr2 = (1 - abs(gam1d) ** 2) * 0.5 / (1 - abs(gam1d) * cob)
    # dr2 = 2 * rr2
    rr1 = dia1 * 0.5
    # coupls = (1 / rr2 - 1) / (1 / rr1 - 1 / rr2)
    # rs = 2 / dr2 - 1
    kapa1 = rr1 / (rr2 - rr1)
    Q01 = QL1 * (1 + kapa1)

    # standard deviations
    sdQL1 = np.sqrt((sig[2].real) ** 2 + sig[2] ** 2)
    sddia1an = np.sqrt(
        sig[0] ** 2 * abs(g[2]) ** (-2)
        + sig[1] ** 2
        + abs(g[0] / (g[2] ** 2)) ** 2 * sig[2] ** 2
    )
    # equi = abs(gam1 - gamc1)
    # avequi = equi.mean()
    # sdequi = equi.std()
    # sddia1st = sdequi * 2
    sddia1 = sddia1an
    sdkapa1 = sddia1 / (2 - dia1) ** 2
    sdQ01 = np.sqrt((1 + kapa1) ** 2 * sdQL1**2 + QL1**2 * sdkapa1**2)

    qname = "Q0" if output is None else f"{output}->Q0"
    fname = "f0" if output is None else f"{output}->f0"
    ret = {
        qname: pint.Quantity(uc.ufloat(Q01, sdQ01)),
        fname: pint.Quantity(uc.ufloat(f011, fres[idia]), freu),
    }
    print(ret)
    return ret
