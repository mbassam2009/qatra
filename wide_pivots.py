"""Find every centre pivot in a 73 x 69 km area of central Qassim and estimate its 2024-25 water use.

Inputs (made in the browser with fetch_wide_s2.js, Microsoft Planetary Computer data API):
  - data/s2_ndvi_max_2025.jpg: the highest Sentinel-2 NDVI of 12 monthly images (Dec 2024 to Nov 2025), tile 38RLQ,
    bbox 43.35-44.08 E, 26.13-26.75 N, about 30 m pixels, NDVI scaled -0.2..0.9 -> 0..255
  - the mean NDVI inside each detected circle, per month (data/wide_pivots.csv, ndvi_01..ndvi_12)

Detection: threshold the max-NDVI image at four levels, fill small holes (the bare pivot point), take local maxima
of the distance transform as circle centres (radius = distance to the edge), keep shapes whose bounding-square
corners are mostly not green (circles, not squares), then remove overlaps.

Water: same as fields.py. Cover = (NDVI - 0.17) / (0.75 - 0.17), daily crop ET = cover x ET0 (NASA POWER),
minus effective rain, / 0.8 pivot efficiency. Likely range x0.85 to x1.17 (config.py).
Check: on 10 of the 14 hand-checked fields, same pattern as Landsat for 8, about 15% less water in total.
"""
import json, math, sys
import numpy as np
import pandas as pd

BB = (43.35, 26.13, 44.08, 26.75)
PIX_M = 29.7


def detect(path="data/s2_ndvi_max_2025.jpg", thresholds=(115, 140, 170, 200)):
    import cv2
    from scipy import ndimage as ndi
    img = cv2.imread(path, 0); H0, W = img.shape
    H = int(round(H0 * 29.908 / 29.699))          # make pixels square (29.7 m) before looking for circles
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LINEAR)
    bl = cv2.GaussianBlur(img, (3, 3), 0.8)
    yy, xx = np.mgrid[-40:41, -40:41]; d = np.hypot(xx, yy)
    cand = []
    for th in thresholds:
        mask = (bl > th).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        lab, n = ndi.label(1 - mask)
        sizes = ndi.sum(1 - mask, lab, range(1, n + 1))
        mask = (mask | np.isin(lab, np.where(sizes <= 40)[0] + 1)).astype(np.uint8)
        dt = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
        for y, x in np.argwhere((dt == ndi.maximum_filter(dt, size=9)) & (dt >= 6)):
            R = dt[y, x] + 0.5
            if R > 24 or y < 41 or x < 41 or y > H - 42 or x > W - 42:
                continue
            m = mask[y - 40:y + 41, x - 40:x + 41].astype(float)
            corner = m[(np.abs(xx) <= R) & (np.abs(yy) <= R) & (d > R * 1.12)]
            if m[d <= R].mean() > 0.9 and corner.mean() < 0.45:
                cand.append((float(x), float(y), float(R)))
    cand.sort(key=lambda c: -c[2])
    sel = []
    for c in cand:
        if all(math.hypot(c[0] - s[0], c[1] - s[1]) > 0.8 * (c[2] + s[2]) for s in sel):
            sel.append(c)
    return [dict(lon=BB[0] + x / W * (BB[2] - BB[0]), lat=BB[3] - y / H * (BB[3] - BB[1]), radius_m=R * PIX_M)
            for x, y, R in sel]


def water(csv="data/wide_pivots.csv"):
    import model, fields
    from config import PIVOT_EFFICIENCY
    df = pd.read_csv(csv)
    w = model.load_weather(); yr = w.loc["2024-10-01":"2025-09-30"]
    out = []
    for _, r in df.iterrows():
        mon = pd.Series([r[f"ndvi_{m:02d}"] for m in fields.MONTHS], index=fields.MONTHS)
        cover = ((mon - 0.17) / 0.58).clip(0, 1).interpolate(limit_direction="both").fillna(0)
        kc = yr.index.month.map(dict(zip(fields.MONTHS, cover.values)))
        m3ha = np.maximum(0, np.asarray(kc) * yr.et0.values - yr.rain_eff.values).sum() / PIVOT_EFFICIENCY * 10
        out.append((fields.pattern(cover.values), m3ha, m3ha * r.ha))
    df["pattern_check"], df["m3ha_check"], df["total_check"] = zip(*out)
    return df


if __name__ == "__main__":
    df = water()
    from config import RANGE_LOW, RANGE_HIGH
    t = df.total_check.sum() / 1e6
    print(f"{len(df)} pivots, {df.ha.sum():,.0f} ha, {t:,.0f} M m3/yr (likely {t*RANGE_LOW:,.0f} to {t*RANGE_HIGH:,.0f})")
    print(df.groupby("pattern_check").agg(n=("id", "size"), water=("total_check", "sum")))
