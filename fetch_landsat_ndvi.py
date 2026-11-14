"""Landsat 8/9 NDVI history for both pivot fields, from Microsoft Planetary Computer (no login needed).

Uses the Landsat Collection 2 Level-2 archive (NASA/USGS) through the Planetary Computer STAC API
and its data API (zonal statistics over each field ring). Output: data/ndvi_raw.csv and data/ndvi_clean.csv

Run:  python fetch_landsat_ndvi.py
"""
import math

import pandas as pd
import requests

from config import FIELDS, RING_INNER_M, EDGE_MARGIN_M

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
STATS = "https://planetarycomputer.microsoft.com/api/data/v1/item/statistics"
# NDVI from raw DNs: reflectance = DN * 0.0000275 - 0.2, so the offsets give the -14545.45 term
EXPR = "(nir08_b1-red_b1)/(nir08_b1+red_b1-14545.45);blue_b1*0.0000275-0.2"


def ring(lon, lat, r_in, r_out, n=48):
    k, kl = 111320, 111320 * math.cos(math.radians(lat))
    outer = [[lon + r_out * math.cos(2 * math.pi * i / n) / kl, lat + r_out * math.sin(2 * math.pi * i / n) / k]
             for i in range(n + 1)]
    inner = [[lon + r_in * math.cos(2 * math.pi * i / n) / kl, lat + r_in * math.sin(2 * math.pi * i / n) / k]
             for i in range(n, -1, -1)]
    return {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [outer, inner]}}


def search(lon, lat):
    body = {"collections": ["landsat-c2-l2"], "intersects": {"type": "Point", "coordinates": [lon, lat]},
            "datetime": "2015-01-01T00:00:00Z/2025-12-31T23:59:59Z",
            "query": {"eo:cloud_cover": {"lt": 40}, "platform": {"in": ["landsat-8", "landsat-9"]}}, "limit": 250}
    items, url = [], STAC
    while url:
        r = requests.post(url, json=body, timeout=60).json()
        items += r["features"]
        nxt = next((l for l in r.get("links", []) if l["rel"] == "next"), None)
        url, body = (nxt["href"], nxt.get("body", body)) if nxt else (None, None)
    return items


def main():
    lon = sum(f["lon"] for f in FIELDS.values()) / len(FIELDS)
    lat = sum(f["lat"] for f in FIELDS.values()) / len(FIELDS)
    items = search(lon, lat)
    print(len(items), "Landsat scenes")
    rows = []
    for it in items:
        for key, f in FIELDS.items():
            feat = ring(f["lon"], f["lat"], RING_INNER_M, f["radius_m"] - EDGE_MARGIN_M)
            r = requests.post(STATS, params={"collection": "landsat-c2-l2", "item": it["id"],
                                             "expression": EXPR, "asset_as_band": "false"},
                              json=feat, timeout=120)
            if not r.ok:
                continue
            s = list(r.json()["properties"]["statistics"].values())
            n, b = s[0], s[1]
            rows.append({"date": it["properties"]["datetime"][:10], "field": key,
                         "platform": it["properties"]["platform"], "scene_cloud": it["properties"]["eo:cloud_cover"],
                         "ndvi_mean": n["mean"], "ndvi_median": n["median"], "ndvi_std": n["std"],
                         "blue_mean": b["mean"], "blue_p98": b["percentile_98"], "pixels": n["valid_pixels"]})
    d = pd.DataFrame(rows).sort_values(["date", "field"])
    d.to_csv("data/ndvi_raw.csv", index=False)
    # Bright bare desert soil reaches ~0.17 blue reflectance on clear days; clouds are brighter.
    d[d.blue_mean <= 0.18].to_csv("data/ndvi_clean.csv", index=False)
    print("saved", len(d), "rows")


if __name__ == "__main__":
    main()
