"""FAO-56 Penman-Monteith reference evapotranspiration (ET0), daily.

Reference: Allen et al. 1998, FAO Irrigation and Drainage Paper 56, Chapter 3.
Inputs are daily values. Output is ET0 in mm/day.
"""
import numpy as np


def sat_vp(t):
    """Saturation vapour pressure (kPa) at temperature t (deg C). FAO-56 Eq. 11."""
    return 0.6108 * np.exp(17.27 * t / (t + 237.3))


def extraterrestrial_radiation(lat_deg, doy):
    """Ra (MJ m-2 day-1) for latitude (deg) and day of year. FAO-56 Eq. 21-25."""
    phi = np.radians(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi / 365 * doy)
    delta = 0.409 * np.sin(2 * np.pi / 365 * doy - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    gsc = 0.0820
    return (24 * 60 / np.pi) * gsc * dr * (
        ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws)
    )


def et0_pm(tmax, tmin, rh_mean, u2, rs, lat_deg, doy, elev_m):
    """Daily FAO-56 Penman-Monteith ET0 (mm/day).

    tmax, tmin : air temperature at 2 m (deg C)
    rh_mean    : mean relative humidity (%)
    u2         : wind speed at 2 m (m/s)
    rs         : incoming solar radiation (MJ m-2 day-1)
    lat_deg    : latitude (deg)
    doy        : day of year (1-366)
    elev_m     : elevation (m)
    """
    tmean = (tmax + tmin) / 2
    p = 101.3 * ((293 - 0.0065 * elev_m) / 293) ** 5.26          # Eq. 7
    gamma = 0.000665 * p                                          # Eq. 8
    delta = 4098 * sat_vp(tmean) / (tmean + 237.3) ** 2           # Eq. 13
    es = (sat_vp(tmax) + sat_vp(tmin)) / 2                        # Eq. 12
    ea = rh_mean / 100 * es                                       # Eq. 19
    ra = extraterrestrial_radiation(lat_deg, doy)
    rso = (0.75 + 2e-5 * elev_m) * ra                             # Eq. 37
    rns = (1 - 0.23) * rs                                         # Eq. 38
    sigma = 4.903e-9
    rnl = sigma * (((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2) \
        * (0.34 - 0.14 * np.sqrt(ea)) \
        * (1.35 * np.clip(rs / rso, 0, 1) - 0.35)                 # Eq. 39
    rn = rns - rnl                                                # Eq. 40
    g = 0.0                                                       # daily soil heat flux ~ 0
    num = 0.408 * delta * (rn - g) + gamma * (900 / (tmean + 273)) * u2 * (es - ea)
    den = delta + gamma * (1 + 0.34 * u2)
    return num / den                                              # Eq. 6
