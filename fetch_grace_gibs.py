"""GRACE / GRACE-FO water storage change over the Qassim region, 2002-2022.

Source: NASA JPL GRACE and GRACE-FO mascon (CRI) liquid water equivalent thickness, as served by
NASA GIBS (layer GRACE_Tellus_Liquid_Water_Equivalent_Thickness_Mascon_CRI). Each monthly map of a
3 x 3 degree box (25-28 N, 42-45 E) is requested as a small PNG, and each pixel colour is turned back
into its value with the layer's GIBS colour map (0.25 cm bins). No login needed.

Limits: GIBS serves this layer to July 2022; values are colour-map bins (0.25 cm); a mascon is ~3 deg,
so this is a regional signal, not one farm. The full JPL file (to 2026) needs an Earthdata download.

Output: data/grace_qassim.csv  (date, lwe_cm relative to the JPL 2004-2009 baseline)
"""
import io
import re
from datetime import date

import pandas as pd
import requests
from PIL import Image

WMS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
LAYER = "GRACE_Tellus_Liquid_Water_Equivalent_Thickness_Mascon_CRI"
CMAP = f"https://gibs.earthdata.nasa.gov/colormaps/v1.3/{LAYER}.xml"


def colour_map():
    xml = requests.get(CMAP, timeout=60).text
    m = {}
    for r, g, b, lo, hi in re.findall(r'rgb="(\d+),(\d+),(\d+)"[^>]*value="\[([^,]+),([^)\]]+)[)\]]"', xml):
        lo, hi = float(lo), float(hi)
        lo = hi if lo == float("-inf") else lo
        hi = lo if hi == float("inf") else hi
        m[(int(r), int(g), int(b))] = (lo + hi) / 2
    return m


def dates():
    cap = requests.get(WMS, params={"SERVICE": "WMS", "REQUEST": "GetCapabilities", "VERSION": "1.3.0"}, timeout=120).text
    seg = cap[cap.index(f"<Name>{LAYER}"):]
    dim = re.search(r'<Dimension name="time"[^>]*>([^<]*)</Dimension>', seg).group(1)
    out = set()
    for iv in dim.split(","):
        a, b, p = iv.split("/")
        if p == "P1M":
            for d in pd.date_range(a, b, freq="MS"):
                out.add(d.date().isoformat())
        else:
            out.add(a)
    return sorted(out)


def main():
    cmap = colour_map()
    rows = []
    for d in dates():
        png = requests.get(WMS, params={"SERVICE": "WMS", "REQUEST": "GetMap", "VERSION": "1.3.0", "LAYERS": LAYER,
                                        "CRS": "EPSG:4326", "BBOX": "25,42,28,45", "WIDTH": 12, "HEIGHT": 12,
                                        "FORMAT": "image/png", "TIME": d}, timeout=60).content
        im = Image.open(io.BytesIO(png)).convert("RGBA")
        vals = [cmap[p[:3]] for p in im.getdata() if p[3] > 200 and p[:3] in cmap]
        if vals:
            rows.append((d, round(sum(vals) / len(vals), 2)))
    pd.DataFrame(rows, columns=["date", "lwe_cm"]).to_csv("data/grace_qassim.csv", index=False)
    print(len(rows), "months saved")


if __name__ == "__main__":
    main()
