"""
.. codeauthor::
    Peter Kraus,
    Darko Kajfez

Provides several functions for processing reflection coefficient traces. Includes
a few trace pruning functions, as well as several algorithms for fitting of quality
factors to the reflection trace data. The use of the peak-height based pruning via
:func:`prune_cutoff` and Kajfez's circle fitting algorithm [Kajfez1994]_ via
:func:`qf_kajfez` is recommended.

.. rubric:: Functions

.. autosummary::

    prune_cutoff
    prune_gradient
    qf_kajfez
    qf_naive
    qf_lorentz


.. [Kajfez1994] Kajfez, D.
   *Linear fractional curve fitting for measurement of high Q factors*, IEEE
   Transactions on Microwave Theory and Techniques **1994**, *42*, 1149 - 1153,
   DOI: https://doi.org/10.1109/22.299749


"""
import pint
import numpy as np
import uncertainties as uc
from scipy.optimize import curve_fit

from dgpost.utils.helpers import separate_data, load_data


def _find_peak(near, absgamma, freq) -> int:
    if near is None:
        logmag = -10 * np.log10(absgamma)
        return np.argmax(logmag)
    else:
        dp = len(freq) // 10
        idx = np.argmax(freq > near)
        s = max(0, idx - dp)
        e = min(len(freq), idx + dp)
        logmag = -10 * np.log10(absgamma[s:e])
        return s + np.argmax(logmag)


@load_data(
    ("real", None, list),
    ("imag", None, list),
    ("freq", "Hz", list),
    ("near", "Hz"),
)
def prune_cutoff(
    real: pint.Quantity,
    imag: pint.Quantity,
    freq: pint.Quantity,
    near: pint.Quantity = None,
    cutoff: float = 0.4,
    output: str = "pruned",
) -> dict[str, pint.Quantity]:
    """
    Cutoff-based reflection coefficient trace prune.

    Prunes the reflection trace around a single peak position in :math:`|\\Gamma|`.
    The pruning is performed using a cutoff value in the :math:`|\\Gamma|`. Should
    be used with :func:`qf_kajfez`. Unless a frequency value using ``near`` is
    specified, the pruning is performed around the global maximum in
    :math:`\\log(|\\Gamma|)`.

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

    near
        A frequency used to select the point around which to prune. By default, pruning
        is performed around the highest peak in :math:`\\text{log}|\\Gamma|`. When set,
        pruning will be perfomed around any maximum in :math:`\\text{log}|\\Gamma|` that
        exists within 10% of the trace size on either side of the selected point. This
        means that for a trace size of 20001 points, 2000 points below and 2000 points
        above the point corresponding to the selected frequency will be used to find a
        local maximum.

    cutoff
        Relative peak height below which the reflection trace should be pruned.
        Uses a fraction of normalised :math:`|\\Gamma|`. Defaults to ``0.4``.

    output
        Name for the output namespace. Defaults to ``"pruned"``.

    Returns
    -------
    retvals: dict[str, pint.Quantity]
        A dictionary containing the pruned values of ``real``, ``imag`` and ``freq``
        data stored in namespaced :class:`pint.Quantities`.

    """
    re, _, _ = separate_data(real)
    im, _, _ = separate_data(imag)
    absgamma = np.abs(re + 1j * im)
    pi = _find_peak(near, absgamma, freq)
    max_v = absgamma.max()
    min_v = absgamma[pi]
    norm = (absgamma - min_v) / (max_v - min_v)
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
    ll, lr = (li + 1, ri - 1)
    ret = {}
    ret[f"{output}->imag"] = imag[ll:lr]
    ret[f"{output}->real"] = real[ll:lr]
    ret[f"{output}->freq"] = freq[ll:lr]
    return ret


@load_data(
    ("real", None, list), ("imag", None, list), ("freq", "Hz", list), ("near", "Hz")
)
def prune_gradient(
    real: pint.Quantity,
    imag: pint.Quantity,
    freq: pint.Quantity,
    near: pint.Quantity = None,
    threshold: float = 1e-6,
    output: str = "pruned",
) -> dict[str, pint.Quantity]:
    """
    Gradient-based reflection coefficient trace prune.

    Prunes the reflection trace around a single peak position in :math:`|\\Gamma|`.
    The pruning is performed using the a threshold value in the gradient of
    :math:`|\\Gamma|`. Unless a frequency value using ``near`` is specified, the
    pruning is performed around the global maximum in :math:`\\log(|\\Gamma|)`.

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

    near
        A frequency used to select around which peak to prune. By default, pruning
        is performed around the highest peak in :math:`\\text{log}|\\Gamma|`. When set,
        pruning will be perfomed around any maximum in :math:`\\text{log}|\\Gamma|` that
        exists within 10% of the trace size on either side of the selected point. This
        means that for a trace size of 20001 points, 2000 points below and 2000 points
        above the point corresponding to the selected frequency will be used to find a
        local maximum.

    threshold
        Threshold for the gradient in the :math:`\\text{abs}(\\Gamma)` below which the
        trace is pruned. Defaults to ``1e-6``.

    output
        Name for the output namespace. Defaults to ``"pruned"``.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A dictionary containing the pruned values of ``real``, ``imag`` and ``freq``
        data stored in namespaced :class:`pint.Quantities`.

    """

    re, _, _ = separate_data(real)
    im, _, _ = separate_data(imag)
    absgamma = np.abs(re + 1j * im)
    grad = np.gradient(absgamma)

    pi = _find_peak(near, absgamma, freq)

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
    ll, lr = (li + 1, ri - 1)
    ret = {}
    ret[f"{output}->imag"] = imag[ll:lr]
    ret[f"{output}->real"] = real[ll:lr]
    ret[f"{output}->freq"] = freq[ll:lr]
    return ret


@load_data(
    ("real", None, list),
    ("imag", None, list),
    ("freq", "Hz", list),
)
def qf_kajfez(
    real: pint.Quantity,
    imag: pint.Quantity,
    freq: pint.Quantity,
    iterations: int = 5,
    output: str = None,
) -> dict[str, pint.Quantity]:
    """
    Kajfez's circle-fitting algorithm.

    Adapted with permission from Q0REFL.m, which is a part of [Kajfez1994]_. This
    fitting process attempts to fit a circle to a near-circular section of points
    on a Smith's chart. It's robust, quick, and reliable, and produces reasonable
    error estimates.

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

    iterations
        A number of iterations for circle-fitting refinement. Default is ``5``.

    output
        Name for the output namespace. Defaults to no namespace.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        An optionally namespaced dictionary containing the fitted values of
        :math:`Q_0` and :math:`f_0` as :class:`pint.Quantities`.

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
    return ret


@load_data(
    ("real", None, list),
    ("imag", None, list),
    ("freq", "Hz", list),
)
def qf_naive(
    real: pint.Quantity,
    imag: pint.Quantity,
    freq: pint.Quantity,
    output: str = None,
) -> dict[str, pint.Quantity]:
    """
    Naive quality factor fitting algorithm using FWHM.

    This fit finds the central frequency :math:`f_0`, determines the full-width at
    the half-maximum :math:`\\Delta f_{HM}` by linear interpolation, and calculates
    the quality factor using :math:`Q_0 = f_0 / \\Delta f_{HM}`.

    .. note::

        This quality factor fitting algorithm is unreliable and has been implemented
        only for testing purposes. Use :func:`qf_kajfez` for any production runs!

    real
        A :class:`pint.Quantity` object containing the real part of the reflection
        coefficient data, :math:`\\text{Re}(\\Gamma)`. Unitless.

    imag
        A :class:`pint.Quantity` object containing the imaginary part of the reflection
        coefficient data, :math:`\\text{Im}(\\Gamma)`. Unitless.

    freq
        A :class:`pint.Quantity` object containing the frequencies :math:`f`
        corresponding to the reflection coefficient data. Defaults to ``Hz``.

    output
        Name for the output namespace. Defaults to no namespace.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        An optionally namespaced dictionary containing the fitted values of
        :math:`Q_0` and :math:`f_0` as :class:`pint.Quantities`.

    """
    re, _, _ = separate_data(real)
    im, _, _ = separate_data(imag)
    fr, fs, fu = separate_data(freq)
    absgamma = np.abs(re + 1j * im)
    maxg = absgamma.max()
    ming = absgamma.min()
    absgamma = (absgamma - maxg) / (ming - maxg)
    ai = np.argmax(absgamma)
    lf = np.interp(0.5, absgamma[:ai], fr[:ai])
    rf = np.interp(0.5, absgamma[ai:][::-1], fr[ai:][::-1])
    f0 = pint.Quantity(uc.ufloat(fr[ai], fs[ai]), fu)
    Q0 = f0 / pint.Quantity(uc.ufloat(rf, fs[ai]) - uc.ufloat(lf, fs[ai]), fu)
    qname = "Q0" if output is None else f"{output}->Q0"
    fname = "f0" if output is None else f"{output}->f0"
    return {qname: Q0, fname: f0}


@load_data(
    ("real", None, list),
    ("imag", None, list),
    ("freq", "Hz", list),
)
def qf_lorentz(
    real: pint.Quantity,
    imag: pint.Quantity,
    freq: pint.Quantity,
    output: str = None,
) -> dict[str, pint.Quantity]:
    """
    Quality factor fitting algorithm using Lorentzian approximation.

    This fit fits a Lorentzian to the (pruned) data. The :math:`f_0 = x_0`, and the
    :math:`Q_0` is calculated from :math:`x_0 / \\Delta x = x_0 / (2\\gamma)`.
    Uncertainties of :math:`f_0` and :math:`Q_0` are calculated using the
    covariance matrix of the fit of :math:`L(x)` to :math:`|\\Gamma(f)|`.

    .. note::

        This quality factor fitting algorithm is unreliable and has been implemented
        only for testing purposes. Use :func:`qf_kajfez` for any production runs!

    real
        A :class:`pint.Quantity` object containing the real part of the reflection
        coefficient data, :math:`\\text{Re}(\\Gamma)`. Unitless.

    imag
        A :class:`pint.Quantity` object containing the imaginary part of the reflection
        coefficient data, :math:`\\text{Im}(\\Gamma)`. Unitless.

    freq
        A :class:`pint.Quantity` object containing the frequencies :math:`f`
        corresponding to the reflection coefficient data. Defaults to ``Hz``.

    output
        Name for the output namespace. Defaults to no namespace.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        An optionally namespaced dictionary containing the fitted values of
        :math:`Q_0` and :math:`f_0` as :class:`pint.Quantities`.

    """

    def lorentzian(x, a, x0, gam, c):
        return a * (gam**2 / ((x - x0) ** 2 + gam**2)) + c

    re, _, _ = separate_data(real)
    im, _, _ = separate_data(imag)
    fr, _, fu = separate_data(freq)
    absgamma = np.abs(re + 1j * im)
    popt, pcov = curve_fit(
        lorentzian,
        fr,
        absgamma,
        sigma=absgamma,
        absolute_sigma=True,
        p0=[-0.5, fr[np.argmin(absgamma)], 1e5, 1],
    )
    perr = np.sqrt(np.diag(pcov))
    x0 = uc.ufloat(popt[1], perr[1])
    gam = uc.ufloat(popt[2], perr[2])
    f0 = pint.Quantity(x0, fu)
    Q0 = pint.Quantity(x0 / (2 * gam))
    qname = "Q0" if output is None else f"{output}->Q0"
    fname = "f0" if output is None else f"{output}->f0"
    return {qname: Q0, fname: f0}
