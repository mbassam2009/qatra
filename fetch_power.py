"""Download daily NASA POWER weather for the field and save to data/power.csv.

Run on your laptop:  python fetch_power.py
Edit FIELD in config.py first.
"""
import pandas as pd
import requests

from config import FIELD, START, END

PARAMS = ["T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"]
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def fetch():
    r = requests.get(URL, params={
        "parameters": ",".join(PARAMS),
        "community": "AG",
        "latitude": FIELD["lat"],
        "longitude": FIELD["lon"],
        "start": START,
        "end": END,
        "format": "JSON",
    }, timeout=120)
    r.raise_for_status()
    js = r.json()
    p = js["properties"]["parameter"]
    df = pd.DataFrame({k: pd.Series(v) for k, v in p.items()})
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.replace(-999, pd.NA).astype(float)
    df = df.rename(columns={
        "T2M_MAX": "tmax", "T2M_MIN": "tmin", "RH2M": "rh",
        "WS2M": "u2", "ALLSKY_SFC_SW_DWN": "rs", "PRECTOTCORR": "rain",
    })
    # POWER gives elevation in the response; keep it for ET0
    elev = js.get("geometry", {}).get("coordinates", [None, None, None])[2]
    df.attrs["elev"] = elev
    df.index.name = "date"
    df.to_csv("data/power.csv")
    if elev is not None:
        open("data/elev.txt", "w").write(str(elev))
    print(f"Saved {len(df)} days to data/power.csv (POWER elevation: {elev} m)")
    print(df.describe().round(1))


if __name__ == "__main__":
    fetch()
