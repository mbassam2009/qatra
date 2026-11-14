"""All pivot fields: what each grew in crop year 2024-25 (Landsat) and the water it used.

Current water use is estimated from the field's own Landsat greenness, month by month:
  cover = (NDVI - 0.17) / (0.75 - 0.17), clipped to 0-1   (0.17 = bare sand here, 0.75 = full crop)
  daily crop ET = cover x ET0 (a fully covered crop uses about the reference ET; FAO-56 mid-season Kc ~1)
  pumped water  = sum(max(0, crop ET - effective rain)) / pivot efficiency
This is our central estimate (FAO-56 style, which matches a ground measurement on a Saudi alfalfa pivot).
The range (x0.85 to x1.17) covers crop water +/-10% and pivot efficiency 75-85% (see config.py).

The pattern label (year-round, winter crop, summer crop, not farmed) comes from simple rules on the
same monthly cover. Output: data/fields.json
"""
import json
import math

import numpy as np
import pandas as pd

import model
from config import PIVOT_EFFICIENCY, RANGE_LOW, RANGE_HIGH

ECO_FACTOR = 0.37   # what ECOSTRESS would give (ET/ET0 0.35 on green fields); kept only for comparison, see check_ecostress.py
MONTHS = [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9]

FIELDS = [  # id, lat, lon, radius_m  (Field 1-2 picked by hand; 3-14 found by circle detection on Sentinel-2)
    ("pivot1", 26.293592, 43.718483, 326), ("pivot2", 26.299203, 43.726511, 250),
    ("p5", 26.298606, 43.7432, 308), ("p6", 26.276827, 43.69168, 257), ("p7", 26.281442, 43.68048, 310),
    ("p8", 26.260096, 43.73776, 291), ("p9", 26.277115, 43.75664, 310), ("p10", 26.328173, 43.73872, 247),
    ("p11", 26.261683, 43.68752, 417), ("p12", 26.333942, 43.7024, 243), ("p13", 26.288221, 43.67104, 347),
    ("p14", 26.337548, 43.73056, 203), ("p15", 26.279279, 43.6696, 275), ("p16", 26.343606, 43.70048, 255),
]

PATTERNS = {
    "year": ("Green all year", "أخضر طوال العام"),
    "winter": ("Winter crop, bare summer", "محصول شتوي وصيف بلا زراعة"),
    "long": ("Green autumn to early summer, bare late summer", "أخضر من الخريف إلى أوائل الصيف، ثم بلا زراعة"),
    "summer": ("Summer crop only", "محصول صيفي فقط"),
    "two": ("Two crops a year", "محصولان في السنة"),
    "part": ("Only parts of the circle farmed", "جزء من الدائرة مزروع فقط"),
    "none": ("Mostly bare this year", "شبه متروك هذا العام"),
}


def pattern(cover):
    c = dict(zip(MONTHS, cover))
    winter = max(c[1], c[2], c[3])
    summer = np.mean([c[6], c[7], c[8], c[9]])
    if max(cover) < 0.6:
        return "none"
    if sum(0.25 < x < 0.75 for x in cover) >= 6:
        return "part"
    if winter >= 0.6 and summer < 0.6 and sum(x >= 0.5 for x in cover) >= 7:
        return "long"
    if winter >= 0.6 and summer >= 0.6:
        gap = min(c[4], c[5], c[6]) < 0.35
        return "two" if gap else "year"
    if winter >= 0.6:
        return "winter"
    if summer >= 0.6:
        return "summer"
    return "none"


def main():
    w = model.load_weather()
    yr = w.loc["2024-10-01":"2025-09-30"]
    nd = pd.read_csv("data/ndvi_clean.csv", parse_dates=["date"])
    out = []
    for i, (fid, lat, lon, r) in enumerate(FIELDS, start=1):
        g = nd[nd.field == fid]
        s = g[(g.date >= "2024-10-01") & (g.date < "2025-10-01")]
        mon = s.groupby(s.date.dt.month).ndvi_median.max().reindex(MONTHS)
        cover = ((mon - 0.17) / (0.75 - 0.17)).clip(0, 1).interpolate(limit_direction="both").fillna(0)
        kc = yr.index.month.map(dict(zip(MONTHS, cover.values)))
        need = np.maximum(0, np.asarray(kc) * yr.et0.values - yr.rain_eff.values)
        m3ha = need.sum() / PIVOT_EFFICIENCY * 10
        monthly = pd.Series(need, index=yr.index).groupby(yr.index.month).sum().reindex(range(1, 13)) / PIVOT_EFFICIENCY * 10
        ha = math.pi * r ** 2 / 1e4
        pat = pattern(cover.values)
        hist = g.sort_values("date")
        out.append({
            "id": fid, "n": i, "lat": lat, "lon": lon, "radius_m": r, "ha": round(ha, 1),
            "pattern": pat, "pattern_en": PATTERNS[pat][0], "pattern_ar": PATTERNS[pat][1],
            "cover": [round(x, 2) for x in cover.values],
            "now_m3ha": round(m3ha), "now_low_m3ha": round(m3ha * RANGE_LOW), "now_high_m3ha": round(m3ha * RANGE_HIGH),
            "now_total": round(m3ha * ha), "now_low_total": round(m3ha * ha * RANGE_LOW),
            "now_high_total": round(m3ha * ha * RANGE_HIGH), "now_ecostress_total": round(m3ha * ha * ECO_FACTOR),
            "monthly_m3ha": [round(x) for x in monthly.values],
            "ndvi": [[d.strftime("%Y-%m-%d"), round(v, 3)] for d, v in zip(hist.date, hist.ndvi_median)],
        })
        print(f"Field {i:2d} {fid:7s} {ha:5.1f} ha  {PATTERNS[pat][0]:26s} now {m3ha:7,.0f} m3/ha  ({m3ha*ha:10,.0f} m3)")
    json.dump(out, open("data/fields.json", "w"), separators=(",", ":"))


if __name__ == "__main__":
    main()
