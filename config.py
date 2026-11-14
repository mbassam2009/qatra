"""Field settings. Two neighbouring active pivots in Qassim, about 1 km apart (Google Maps, 14 Nov 2026)."""

FIELDS = {
    "pivot1": {
        "name": "Field 1 (326 m radius)",
        "lat": 26.293592,    # 26°17'36.93"N
        "lon": 43.718483,    # 43°43'06.54"E
        "radius_m": 326,
    },
    "pivot2": {
        "name": "Field 2 (250 m radius)",
        "lat": 26.299203,    # 26°17'57.13"N
        "lon": 43.726511,    # 43°43'35.44"E
        "radius_m": 250,
    },
}

# Weather point: both fields share one NASA POWER grid cell, so one download covers both.
FIELD = {
    "name": "Two pivot fields, Qassim (about 36 km NW of Unaizah)",
    "lat": 26.2964,
    "lon": 43.7225,
    "elev_m": None,      # None = use the elevation NASA POWER returns (saved by fetch_power.py)
}

# Ring used for satellite averages: skip the bare pivot point in the middle
# and stay ~45 m inside the field edge (Landsat pixels are 30 m).
RING_INNER_M = 60
EDGE_MARGIN_M = 45

START = "20150101"
END = "20251231"

PIVOT_EFFICIENCY = 0.80  # share of pumped water the crop actually uses (assumption; check)
