"""Water need, heat risk and soil score for each rotation.

Method (FAO-56 single crop coefficient):
  daily crop ET  ETc = Kc(day) * ET0              (ET0 from NASA POWER weather, FAO-56 Penman-Monteith)
  daily need     = max(0, ETc - effective rain)   (rain from NASA POWER, MERRA-2 / IMERG based)
  pumped water   = sum(need) / pivot efficiency
  1 mm over 1 ha = 10 m3
"""
import numpy as np
import pandas as pd

from config import FIELD, PIVOT_EFFICIENCY
from crops import CROPS, ROTATIONS
from et0 import et0_pm


def field_elevation():
    if FIELD["elev_m"] is not None:
        return FIELD["elev_m"]
    try:
        return float(open("data/elev.txt").read())
    except (FileNotFoundError, ValueError):
        return 650.0


def load_weather(path="data/power.csv"):
    df = pd.read_csv(path, parse_dates=["date"], index_col="date").dropna()
    df["et0"] = et0_pm(df.tmax, df.tmin, df.rh, df.u2, df.rs,
                       FIELD["lat"], df.index.dayofyear, field_elevation())
    # effective rain: small daily showers mostly evaporate (assumption)
    df["rain_eff"] = np.where(df.rain > 5, 0.8 * df.rain, 0.0)
    return df


def kc_curve(crop):
    """Daily Kc array following the FAO-56 four-stage shape."""
    ini, mid, end = CROPS[crop]["kc"]
    l_ini, l_dev, l_mid, l_late = CROPS[crop]["stages"]
    curve = [ini] * l_ini
    curve += list(np.linspace(ini, mid, l_dev, endpoint=False))
    curve += [mid] * l_mid
    curve += list(np.linspace(mid, end, l_late))
    return np.array(curve)


def crop_season(weather, crop, year, month, day):
    kc = kc_curve(crop)
    if len(kc) == 0:
        return pd.DataFrame()
    days = pd.date_range(pd.Timestamp(year=year, month=month, day=day), periods=len(kc), freq="D")
    w = weather.reindex(days)
    if w.et0.isna().any():
        return None  # outside the weather record
    out = pd.DataFrame(index=days)
    out["crop"] = crop
    out["kc"] = kc
    out["etc"] = kc * w.et0.values
    out["need"] = np.maximum(0, out.etc - w.rain_eff.values)
    out["tmax"] = w.tmax.values
    return out


def soil_score(crops):
    """Simple, transparent 0-4 score (shown in the app)."""
    days_covered = sum(sum(CROPS[c]["stages"]) for c in crops)
    score = 0
    score += 2 if any(CROPS[c]["legume"] for c in crops) else 0        # adds nitrogen
    score += 1 if days_covered >= 240 else 0                             # soil covered 8+ months
    score += 1 if any(CROPS[c]["residue"] for c in crops) else 0         # cereal stubble protects soil
    return score


def season_days(weather, key, y):
    """Daily table for one crop year (Oct y to Sep y+1). None if outside the record."""
    parts = []
    for crop, m, d in ROTATIONS[key]["plan"]:
        sow_year = y if m >= 10 else y + 1
        s = crop_season(weather, crop, sow_year, m, d)
        if s is None:
            return None
        parts.append(s)
    return pd.concat(parts) if parts else pd.DataFrame()


def evaluate(weather, key, years):
    rot = ROTATIONS[key]
    rows, monthly = [], []
    for y in years:
        s = season_days(weather, key, y)
        if s is None:
            continue
        hot = 0
        for crop in s.crop.unique():
            lim = CROPS[crop]["heat_c"]
            if lim is not None:
                hot += int((s[s.crop == crop].tmax > lim).sum())
        rows.append({"season": f"{y}-{str(y + 1)[2:]}", "water_mm": s.need.sum(), "hot_days": hot})
        if len(s):
            m = (s.need.groupby(s.index.month).sum() / PIVOT_EFFICIENCY * 10)
            monthly.append(m)
    res = pd.DataFrame(rows)
    res["water_m3_ha"] = res.water_mm / PIVOT_EFFICIENCY * 10
    mon = pd.concat(monthly, axis=1).fillna(0).mean(axis=1).reindex(range(1, 13), fill_value=0) if monthly \
        else pd.Series(0.0, index=range(1, 13))
    crops = [c for c, _, _ in rot["plan"]]
    return {
        "key": key,
        "name": rot["name"],
        "short": rot["short"],
        "why": rot["why"],
        "crops": crops,
        "seasons": len(res),
        "water_m3_ha": res.water_m3_ha.mean(),
        "water_min": res.water_m3_ha.min(),
        "water_max": res.water_m3_ha.max(),
        "hot_days": res.hot_days.mean(),
        "soil_score": soil_score(crops),
        "per_season": res,
        "monthly_m3_ha": mon,
    }


def compare(weather):
    first, last = weather.index.year.min(), weather.index.year.max()
    years = range(first, last)  # crop years Oct y - Sep y+1 fully inside the record
    res = [evaluate(weather, k, years) for k in ROTATIONS]
    # E: wheat (C) and faba bean (D) in alternate years = the average of the two, year by year
    from crops import ROTATION_E
    c, d = (next(r for r in res if r["key"] == k) for k in ("C", "D"))
    both = pd.concat([c["per_season"].water_m3_ha, d["per_season"].water_m3_ha], axis=1).mean(axis=1)
    res.append({
        "key": "E", "name": ROTATION_E["name"], "short": ROTATION_E["short"], "why": ROTATION_E["why"],
        "crops": ["wheat", "faba_bean"], "seasons": c["seasons"],
        "water_m3_ha": (c["water_m3_ha"] + d["water_m3_ha"]) / 2, "water_min": both.min(), "water_max": both.max(),
        "hot_days": (c["hot_days"] + d["hot_days"]) / 2, "soil_score": ROTATION_E["soil_score"],
        "per_season": None, "monthly_m3_ha": (c["monthly_m3_ha"] + d["monthly_m3_ha"]) / 2,
    })
    return res


if __name__ == "__main__":
    w = load_weather()
    print(f"ET0: mean {w.et0.mean():.1f} mm/day, Jan {w.et0[w.index.month == 1].mean():.1f}, "
          f"Jul {w.et0[w.index.month == 7].mean():.1f}; annual {w.et0.groupby(w.index.year).sum().mean():.0f} mm")
    for r in compare(w):
        print(f"{r['name']:<48} water {r['water_m3_ha']:>7,.0f} m3/ha/yr "
              f"(range {r['water_min']:,.0f}-{r['water_max']:,.0f}), heat days {r['hot_days']:.0f}, "
              f"soil {r['soil_score']}/4, seasons {r['seasons']}")
