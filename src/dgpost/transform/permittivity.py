"""
.. codeauthor::
    Peter Kraus

Provides functions for calculating complex permittivity from resonance
frequencies and quality factors, as well as and various related corrections.

.. rubric:: Functions

.. autosummary::

    ftT_correction
    QtT_correction
    Qec_correction
    real_eps
    imag_eps

.. [Chen2005a] Chen, L.F., Ong, C.K., Neo, C.P., Varadan, V.V., Varadan, V.K.
   *Resonant-Perturbation Methods* in *Microwave Electronics*, John Wiley & Sons,
   2005, Chichester, UK,
   DOI: https://doi.org/10.1002/0470020466.ch6

.. [Chao2013a] Chao, H.-W., Chang, T.-H.
   *A modified calibration method for complex permittivity measurement*, Review
   of Scientific Instruments **2013**, **84**, 084704,
   DOI: https://doi.org/10.1063/1.4817635

.. [Cuenca2017] Cuenca, J.A., Slocombe, D.R., Porch, A.
   *Temperature Correction for Cylindrical Cavity Perturbation Measurements*,
   IEEE Transactions on Microwave Theory and Techniques **2017**, **65**, 2153-2161,
   DOI: https://doi.org/10.1109/TMTT.2017.2652462

.. [Cuenca2017c] Cuenca, J.A., Slocombe, D.R., Porch, A.
   *Corrections to "Temperature Correction for Cylindrical Cavity Perturbation Measurements"*,
   IEEE Transactions on Microwave Theory and Techniques **2017**, **65**, 5078,
   DOI: https://doi.org/10.1109/TMTT.2017.2751550

"""

import pint

from dgpost.utils.helpers import load_data


@load_data(
    ("f_nm", "Hz"),
    ("temperature", "celsius"),
    ("f_ref_cm", "Hz"),
    ("f_ref_nm", "Hz"),
    ("temperature_ref", "celsius"),
    ("alpha_c", "1/K"),
    ("k_cm", "1/K"),
    ("k_nm", "1/K"),
)
def ftT_correction(
    f_mnp: pint.Quantity,
    temperature: pint.Quantity,
    f_0n0_ref: pint.Quantity,
    f_mnp_ref: pint.Quantity,
    temperature_ref: pint.Quantity,
    k_err: float = 0.0,
    alpha_c: pint.Quantity = pint.Quantity("23×10⁻⁶ 1/K"),
    k_0n0: pint.Quantity = pint.Quantity("0 1/K"),
    k_mnp: pint.Quantity = pint.Quantity("0 1/K"),
    output: str = "f_e,P",
) -> dict[str, pint.Quantity]:
    """
    Nodal mode correction of resonance frequencies for temperature effects
    based on Cuenca et al. [Cuenca2017]_

    The nodal mode correction exploits the fact that the normalized frequency shift
    :math:`\\frac{f(T) - f(T_\\text{ref})}{f(T_\\text{ref})}` over a shift in temperature
    :math:`\Delta T = T - T_\\text{ref}` is approximately constant, regardless of the mode
    studied.

    The correction also exploits the fact that the temperature-dependency of the frequency is
    proportional mainly to the linear thermal expansion coefficient :math:`\\alpha_c`:

    .. math::

        \\frac{f_{mnp}(T) - f_{mnp}(T_\\text{ref})}{f_{mnp}(T_\\text{ref})} \\approx
        - (\\alpha_c + \\kappa_{mnp}) \\Delta T + \\kappa_{err}

    This makes it possible to approximate the behaviour of the frequency of the sample mode from
    the behaviour of a nodal mode (i.e. a mode not affected by the sample). This is useful, as the
    permittivity is related to the shift of the frequency of the sample mode upon insertion of the
    sample, therefore a proxy for the measurement of the empty cavity is required for operando
    measurements. This proxy can be calculated from the behaviour of the nodal mode and a few
    reference & calibration values.

    For example, for the TM020 and TM210 modes (sample and nodal modes, respectively):

    .. math::

        f_\\text{020,e,p}(t, T) && \\approx f_\\text{020,e}(0, T_\\text{ref})
        \\left(1 + \\frac{f_\\text{210,s}(t, T) - f_\\text{210,e}(0, T_\\text{ref})}
                         {f_\\text{210,e}(0, T_\\text{ref})}\\right) \\\\
        && + (\\kappa_\\text{err} - (\\alpha_c + \\kappa_\\text{210})\\Delta T)
                         f_\\text{210,e}(0, T_\\text{ref}) \\\\
        && - (\\kappa_\\text{err} - (\\alpha_c + \\kappa_\\text{020})\\Delta T)
                         f_\\text{020,e}(0, T_\\text{ref})


    Parameters
    ----------
    f_mnp
        The frequency of the nodal mode, :math:`f_{mnp}(t, T)`. Defaults to Hz.

    temperature
        The temperature :math:`T`. Defaults to °C.

    f_0n0_ref
        The reference frequency of the sample mode, :math:`f_{0n0}(0, T_\\text{ref})`.
        Defaults to Hz.

    f_mnp_ref
        The reference frequency of the nodal mode, :math:`f_{mnp}(0, T_\\text{ref})`.
        Defaults to Hz.

    temperature_ref
        The reference temperature :math:`T_\\text{ref}`. Defaults to °C.

    k_err
        The calibration constant :math:`\\kappa_\\text{err}`. Defaults to 0.

    alpha_c
        The linear temperature expansion constant, :math:`\\alpha_c`. Defaults
        to 23×10⁻⁶ K⁻¹, i.e. aluminium.

    k_0n0
        The calibration constant of the sample mode, :math:`\\kappa_{0n0}`.
        Defaults to 0 K⁻¹.

    k_mnp
        The calibration constant of the nodal mode, :math:`\\kappa_{mnp}`.
        Defaults to 0 K⁻¹.

    output
        Name for the output quantity. Defaults to ``f_e,p``.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A dictionary containing the proxy for the frequency of the empty cavity,
        :math:`f_{e,p}(t, T)`.

    """

    d_freq = (f_mnp - f_mnp_ref) / f_mnp_ref
    d_temp = temperature.to("K") - temperature_ref.to("K")

    res = (
        (d_freq + 1) * f_0n0_ref
        + (k_err - (alpha_c + k_mnp) * d_temp) * f_mnp_ref
        - (k_err - (alpha_c + k_0n0) * d_temp) * f_0n0_ref
    )
    return {output: res}


@load_data(
    ("Q_mnp", None),
    ("temperature", "celsius"),
    ("Q_0n0_ref", None),
    ("Q_mnp_ref", None),
    ("temperature_ref", "celsius"),
    ("beta_c", "1/K"),
    ("alpha_c", "1/K"),
    ("k_0n0", "1/K"),
    ("k_mnp", "1/K"),
)
def QtT_correction(
    Q_mnp: pint.Quantity,
    temperature: pint.Quantity,
    Q_mnp_ref: pint.Quantity,
    Q_0n0_ref: pint.Quantity,
    temperature_ref: pint.Quantity = None,
    k_err: float = 0.0,
    beta_c: pint.Quantity = pint.Quantity("4×10⁻³ 1/K"),
    alpha_c: pint.Quantity = pint.Quantity("23×10⁻⁶ 1/K"),
    k_0n0: pint.Quantity = pint.Quantity("0 1/K"),
    k_mnp: pint.Quantity = pint.Quantity("0 1/K"),
    output: str = "Q_e,P",
) -> dict[str, pint.Quantity]:
    """
    Nodal mode correction of quality factors for temperature effects,
    based on Cuenca et al. [Cuenca2017]_

    Similar to :func:`ftT_correction`. However, here the temperature effects
    are modelled using both linear expansion coefficient :math:`\\alpha_c`, as well as
    coefficient of resistivity :math:`\\beta_c`:

    .. math::

        \\frac{Q_{mnp}(T) - Q_{mnp}(T_\\text{ref})}{Q_{mnp}(T_\\text{ref})} \\approx
         (\\beta_c - 3\\alpha_c + \\kappa_{mnp}) \\Delta T + \\kappa_{err}


    For example, for the TM020 and TM210 modes (sample and nodal modes, respectively):

    .. math::

        Q_\\text{020,e,p}(t, T) && \\approx Q_\\text{020,e}(0, T_\\text{ref})
        \\left(1 + \\frac{Q_\\text{210,s}(t, T) - Q_\\text{210,e}(0, T_\\text{ref})}
                         {Q_\\text{210,e}(0, T_\\text{ref})}\\right) \\\\
        && + (\\kappa_\\text{err} + (\\beta_c - 3\\alpha_c + \\kappa_\\text{210})\\Delta T)
                         Q_\\text{210,e}(0, T_\\text{ref}) \\\\
        && - (\\kappa_\\text{err} + (\\beta_c - 3\\alpha_c + \\kappa_\\text{020})\\Delta T)
                         Q_\\text{020,e}(0, T_\\text{ref})


    Parameters
    ----------
    Q_mnp
        The quality factor of the nodal mode, :math:`Q_{mnp}(t, T)`. Unitless.

    temperature
        The temperature :math:`T`. Defaults to °C.

    Q_0n0_ref
        The reference quality factor of the sample mode, :math:`Q_{0n0}(0, T_\\text{ref})`.
        Unitless.

    Q_mnp_ref
        The reference quality factor of the nodal mode, :math:`Q_{mnp}(0, T_\\text{ref})`.
        Unitless.

    temperature_ref
        The reference temperature :math:`T_\\text{ref}`. Defaults to °C.

    k_err
        The calibration constant :math:`\\kappa_\\text{err}`. Defaults to 0.

    alpha_c
        The linear temperature expansion constant, :math:`\\alpha_c`. Defaults
        to 23×10⁻⁶ K⁻¹, i.e. aluminium.

    beta_c
        The coefficient of resistivity, :math:`\\beta_c`. Defaults to 4×10⁻³ K⁻¹,
        i.e. aluminium.

    k_0n0
        The calibration constant of the sample mode, :math:`\\kappa_{0n0}`.
        Defaults to 0 K⁻¹.

    k_mnp
        The calibration constant of the nodal mode, :math:`\\kappa_{mnp}`.
        Defaults to 0 K⁻¹.

    output
        Name for the output quantity. Defaults to ``Q_e,p``.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A dictionary containing the proxy for the frequency of the empty cavity,
        :math:`Q_{e,p}(t, T)`.

    """
    d_Q = (Q_mnp - Q_mnp_ref) / Q_mnp_ref
    d_temp = temperature.to("K") - temperature_ref.to("K")

    res = (
        (d_Q + 1) * Q_mnp_ref
        + (k_err + (beta_c - 3 * alpha_c + k_mnp) * d_temp) * Q_mnp_ref
        - (k_err + (beta_c - 3 * alpha_c + k_0n0) * d_temp) * Q_0n0_ref
    )
    return {output: res}


@load_data(
    ("Q", None),
    ("eps", None),
    ("Vs", "mm³"),
    ("Vc", "mm³"),
)
def Qec_correction(
    Q_e: pint.Quantity,
    eps: pint.Quantity,
    Vs: pint.Quantity,
    Vc: pint.Quantity,
    output: str = "Q_e,c",
) -> dict[str, pint.Quantity]:
    """
    The modified calibration method of Chao and Chang. [Chao2013a]_

    This formula corrects the quality factor of the empty cavity :math:`Q_e`
    to a corrected value :math:`Q_{e,c}` by taking into account the real
    part of the permittivity :math:`\\varepsilon'` of the inserted sample,
    as well as its volume:

    .. math::

        Q_{e,c} = Q_e \\left(1 + (\\varepsilon' - 1)\\frac{V_s}{V_c}\\right)

    Parameters
    ----------
    Q_e
        The quality factor of the empty cavity, :math:`Q_e`. Unitless.

    eps
        The real part of the permittivity, :math:`\\varepsilon'`. Unitless.

    Vs
        Volume of the sample, :math:`V_s`. Defaults to mm³.

    Vc
        Volume of the cavity, :math:`V_c`. Defaults to mm³.

    output
        Name for the output quantity. Defaults to ``Q_e,c``.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A dictionary containing the corrected quality factor of the
        empty cavity, :math:`Q_{e,c}`.

    """
    ret = Q_e * (1 + (eps - 1) * (Vs / Vc))
    return {output: ret}


@load_data(
    ("f_s", "Hz"),
    ("f_e", "Hz"),
    ("Vc", "mm³"),
    ("Vs", "mm³"),
    ("cal_slope", None),
    ("cal_intercept", None),
)
def real_eps(
    f_s: pint.Quantity,
    f_e: pint.Quantity,
    Vc: pint.Quantity,
    Vs: pint.Quantity,
    cal_slope: float = 1.0,
    cal_intercept: float = None,
    output: str = "eps'",
) -> dict[str, pint.Quantity]:
    """
    The MCPT equation for the real part of the permittivity.

    This equation calculates the real part of the permittivity
    :math:`\\varepsilon'` from the shift in the resonance frequency
    of the cavity upon insertion of the sample:

    .. math ::
       \\varepsilon' = f_\\text{cal}\\left(\\frac{f_s - f_e}{f_e}\\right)
                       \\frac{V_c}{V_s} + 1

    Note that in some literature (e.g. [Chen2005a]_ or [Cuenca2017]_),
    the denominator in the above equation is specified as :math:`f_s`. This
    is not correct, and should be :math:`f_e` as in the above equation,
    see [Cuenca2017c]_ for details.

    In most literature, the calibration function :math:`f_\\text{cal}` is
    simply a multiplication by a calibration constant. Here, we allow for
    specifying a linear calibration function using ``cal_slope`` and
    ``cal_intercept``, which is applied in inverse:

    .. math ::
       f_\\text{cal}(y) = \\frac{y - \\text{cal_intercept}}{\\text{cal_slope}}


    Parameters
    ----------
    f_s
        The resonance frequency of the cavity mode with the sample, :math:`f_s`.
        Defaults to Hz.

    f_e
        The resonance frequency of the cavity mode without the sample, :math:`f_e`.
        Defaults to Hz.

    Vs
        Volume of the sample, :math:`V_s`. Defaults to mm³.

    Vc
        Volume of the cavity, :math:`V_c`. Defaults to mm³.

    cal_slope
        The slope of the calibration function.

    cal_intercept
        The intercept of the calibration function.

    output
        Name for the output quantity. Defaults to ``eps'``.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A dictionary containing the real part of the permittivity,
        :math:`\\varepsilon'`.

    """
    tmp = (f_s - f_e) / f_e
    if cal_intercept is not None:
        cal = (tmp - cal_intercept) / cal_slope
    else:
        cal = tmp / cal_slope
    eps = cal * (Vc / Vs) + 1
    return {output: eps}


@load_data(
    ("Q_s", None),
    ("Q_e", None),
    ("Vc", "mm³"),
    ("Vs", "mm³"),
    ("cal_slope", None),
    ("cal_intercept", None),
)
def imag_eps(
    Q_s: pint.Quantity,
    Q_e: pint.Quantity,
    Vc: pint.Quantity,
    Vs: pint.Quantity,
    cal_slope: float = 1.0,
    cal_intercept: float = None,
    output: str = 'eps"',
) -> dict[str, pint.Quantity]:
    """
    The MCPT equation for the imaginary part of the permittivity.
    [Chen2005a]_ [Cuenca2017]_

    This equation calculates the imaginary part of the permittivity
    :math:`\\varepsilon''` from the change of the quality factor
    of the cavity upon insertion of the sample:

    .. math ::
       \\varepsilon'' = f_\\text{cal}\\left(\\frac{1}{Q_s} - \\frac{1}{Q_e}\\right)
                       \\frac{V_c}{V_s}

    In most literature, the calibration function :math:`f_\\text{cal}` is
    simply a multiplication by a calibration constant. Here, we allow for
    specifying a linear calibration function using ``cal_slope`` and
    ``cal_intercept``, which is applied in inverse:

    .. math ::
       f_\\text{cal}(y) = \\frac{y - \\text{cal_intercept}}{\\text{cal_slope}}



    Parameters
    ----------
    Q_s
        The quality factor of the cavity mode with the sample, :math:`Q_s`.
        Unitless.

    Q_e
        The quality factor of the cavity mode without the sample, :math:`Q_e`.
        Unitless.

    Vs
        Volume of the sample, :math:`V_s`. Defaults to mm³.

    Vc
        Volume of the cavity, :math:`V_c`. Defaults to mm³.

    cal_slope
        The slope of the calibration function.

    cal_intercept
        The intercept of the calibration function.

    output
        Name for the output quantity. Defaults to ``eps"``.

    Returns
    -------
    ret: dict[str, pint.Quantity]
        A dictionary containing the real part of the permittivity,
        :math:`\\varepsilon''`.

    """

    tmp = 1 / Q_s - 1 / Q_e
    if cal_intercept is not None:
        cal = (tmp - cal_intercept) / cal_slope
    else:
        cal = tmp / cal_slope
    eps = cal * (Vc / Vs) * (1 / 2)
    return {output: eps}
