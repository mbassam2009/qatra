"""Compare ECOSTRESS daily ET (ECO_L3T_JET.002, via AppEEARS) with our FAO-56 assumptions.

Input:  data/ecostress_jet_raw.csv  (AppEEARS point sample, 4 points per field, 2019-2025)
Output: data/ecostress_check.csv and a printed summary.

Note on units: AppEEARS lists ETdaily as W/m2, but the values (0 to ~8.5) only make physical sense
as mm/day (1 mm/day of ET is ~28 W/m2), so they are treated as mm/day here.

Method: average the 4 points per field per overpass, pair each overpass with
- NASA POWER reference ET0 for that day (our et0.py)
- the nearest Landsat NDVI for that field within 8 days (crop state: bare < 0.25 < partial < 0.5 < green)
then ET/ET0 is the crop coefficient ECOSTRESS implies, to compare with FAO-56 Kc.
"""
import numpy as np
import pandas as pd

import model


def main():
    e = pd.read_csv("data/ecostress_jet_raw.csv")
    e.columns = ["field", "point", "lat", "lon", "datetime", "tile", "et"]
    e["datetime"] = pd.to_datetime(e.datetime.str.replace(" UTC", ""))
    e["date"] = e.datetime.dt.normalize()
    e["hour_local"] = (e.datetime.dt.hour + 3) % 24
    g = e.groupby(["field", "date"]).agg(et=("et", "mean"), points=("et", "size"),
                                         hour_local=("hour_local", "first")).reset_index()
    w = model.load_weather()
    n = pd.read_csv("data/ndvi_clean.csv", parse_dates=["date"])
    nd = []
    for _, r in g.iterrows():
        s = n[n.field == r.field]
        gap = (s.date - r.date).abs()
        nd.append(s.loc[gap.idxmin(), "ndvi_median"] if gap.min() <= pd.Timedelta(days=8) else np.nan)
    g["ndvi"] = nd
    g["et0"] = g.date.map(w.et0)
    g["kc_obs"] = g.et / g.et0
    g["state"] = pd.cut(g.ndvi, [-1, 0.25, 0.5, 1], labels=["bare", "partial", "green"])
    g.to_csv("data/ecostress_check.csv", index=False)

    v = g.dropna(subset=["ndvi", "kc_obs"])
    v = v[v.et > 0]
    summ = g.groupby("state", observed=True).agg(overpasses=("et", "size"), et_mm=("et", "mean"),
                                                 et0_mm=("et0", "mean"), kc_median=("kc_obs", "median")).round(2)
    print(summ)
    print("Correlation of ECOSTRESS ET/ET0 with Landsat NDVI:", round(v.ndvi.corr(v.kc_obs), 2), f"(n={len(v)})")
    green = g[(g.state == "green") & (g.et > 0)]
    k = green.kc_obs.median()
    print(f"Green-field ET/ET0 median {k:.2f} (IQR {green.kc_obs.quantile(.25):.2f}-{green.kc_obs.quantile(.75):.2f}), "
          f"vs FAO-56 mid-season Kc 0.95-1.15")
    print("By local overpass hour (median ET/ET0):")
    print(v.groupby(pd.cut(v.hour_local, [0, 9, 12, 15, 24])).kc_obs.median().round(2))
    return summ, k


if __name__ == "__main__":
    main()
