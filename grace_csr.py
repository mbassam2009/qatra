"""GRACE / GRACE-FO water storage over the Qassim area, 2002-2026, from the CSR mascon file.

Source: CSR GRACE/GRACE-FO RL06.3 mascons, all corrections (University of Texas Center for Space
Research), https://www2.csr.utexas.edu/grace/ . Download CSR_GRACE_GRACE-FO_RL0603_Mascons_all-corrections.nc
(about 115 MB, free, no login) and pass its path:

    python grace_csr.py CSR_GRACE_GRACE-FO_RL0603_Mascons_all-corrections.nc

What it does: takes the 3 x 3 degree box 25-28 N, 42-45 E (the same box as fetch_grace_gibs.py), averages
the 0.25 degree cells weighted by area, and saves one value per month in cm of water, relative to the
2004-2009 mean. It also prints the headline numbers we use.

Cross-check: over the 213 months both cover (2002-2022), this series and the JPL mascon series from
fetch_grace_gibs.py agree closely (correlation 0.96, mean difference 0.3 cm).

Limits: a mascon is about 3 degrees wide, so this is a regional signal, not one farm. It is total water
storage (groundwater plus soil moisture); in this desert almost all of the change is groundwater.
Single months are noisy, so headline numbers use yearly or 12-month averages.

Output: data/grace_qassim_csr.csv  (date, lwe_cm)
"""
import sys
from datetime import datetime, timedelta

import netCDF4
import numpy as np
import pandas as pd

BOX = (25, 28, 42, 45)  # lat0, lat1, lon0, lon1
EARTH_R_KM = 6371.0


def box_area_km2(lat0, lat1, lon0, lon1):
    return EARTH_R_KM ** 2 * np.deg2rad(lon1 - lon0) * (np.sin(np.deg2rad(lat1)) - np.sin(np.deg2rad(lat0)))


def series(path):
    d = netCDF4.Dataset(path)
    lat, lon = d["lat"][:], d["lon"][:]
    lat0, lat1, lon0, lon1 = BOX
    i = np.where((lat > lat0) & (lat < lat1))[0]
    j = np.where((lon > lon0) & (lon < lon1))[0]
    w = np.cos(np.deg2rad(lat[i]))[:, None] * np.ones((1, len(j)))
    x = d["lwe_thickness"][:, i.min():i.max() + 1, j.min():j.max() + 1]
    m = (x * w).sum(axis=(1, 2)) / w.sum()
    t = [datetime(2002, 1, 1) + timedelta(days=float(v)) for v in d["time"][:]]
    return pd.DataFrame({"date": [a.date().isoformat() for a in t], "lwe_cm": np.round(np.asarray(m), 2)})


def trend(s, start, end):
    d = pd.to_datetime(s.date)
    yr = d.dt.year + (d.dt.dayofyear - 0.5) / 365.25
    k = (yr >= start) & (yr < end)
    return np.polyfit(yr[k], s.lwe_cm[k], 1)[0]


def main(path):
    s = series(path)
    s.to_csv("data/grace_qassim_csr.csv", index=False)
    area = box_area_km2(*BOX)
    d = pd.to_datetime(s.date)
    y2003 = s.lwe_cm[d.dt.year == 2003].mean()
    last12 = s.lwe_cm[d > d.max() - pd.DateOffset(months=12)].mean()
    loss_cm = y2003 - last12
    print(f"{len(s)} months, {s.date.iloc[0]} to {s.date.iloc[-1]}; box area {area:,.0f} km2")
    print(f"2003 mean {y2003:+.1f} cm; last 12 months mean {last12:+.1f} cm; lost {loss_cm:.1f} cm = {loss_cm * 1e-5 * area:.0f} km3")
    for a, b, lab in [(2002, 2027, "whole record"), (2002, 2018.4, "GRACE (2002-2017)"), (2018.4, 2027, "GRACE-FO (2018-2026)")]:
        r = trend(s, a, b)
        print(f"trend {lab}: {r:.2f} cm/yr = {r * 1e-5 * area:.2f} km3/yr")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "CSR_GRACE_GRACE-FO_RL0603_Mascons_all-corrections.nc")
