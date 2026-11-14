"""Crop parameters and the rotations Qatra compares.

Kc and stage lengths: FAO Irrigation and Drainage Paper 56 (Allen et al. 1998),
Table 11 (stage lengths) and Table 12 (single crop coefficients).
  wheat        Kc 0.3 / 1.15 / 0.30   stages 20/50/60/30 (Table 11 row "Calif. Desert, USA", Dec planting,
                                       closest arid-desert analogue; matches Field 2's Landsat green season Dec-Apr)
  pearl millet Kc 0.3 / 1.00 / 0.30   stages 15/25/40/25 (Table 11 row "Pakistan", June planting)
  faba bean    Kc 0.5 / 1.15 / 0.30   stages 20/30/35/15 (Table 11 row "Mediterranean"; dry seed Kc)
  alfalfa      Kc 0.95 all year        (Table 12 "alfalfa hay, averaged cutting effects" mid value,
                                       for an established year-round stand)
Heat limits are APPROXIMATE crop heat-stress thresholds used only to count hot days;
confirm with an agronomist before relying on them.
Sowing dates: wheat Dec 1 and the year-round fodder pattern are taken from the Landsat NDVI
history of the two fields; other dates are typical-season assumptions.
"""

CROPS = {
    "wheat": {
        "label": "Wheat", "kc": (0.30, 1.15, 0.30), "stages": (20, 50, 60, 30),
        "heat_c": 32, "legume": False, "residue": True,
    },
    "pearl_millet": {
        "label": "Pearl millet", "kc": (0.30, 1.00, 0.30), "stages": (15, 25, 40, 25),
        "heat_c": 42, "legume": False, "residue": True,
    },
    "faba_bean": {
        "label": "Faba bean", "kc": (0.50, 1.15, 0.30), "stages": (20, 30, 35, 15),
        "heat_c": 30, "legume": True, "residue": False,
    },
    "alfalfa": {
        "label": "Alfalfa (year-round fodder)", "kc": (0.95, 0.95, 0.95), "stages": (0, 0, 365, 0),
        "heat_c": 40, "legume": True, "residue": False,
    },
    "fallow": {
        "label": "Fallow (no irrigation)", "kc": (0.0, 0.0, 0.0), "stages": (0, 0, 0, 0),
        "heat_c": None, "legume": False, "residue": False,
    },
}

# Each rotation = list of (crop key, sowing month, sowing day) in one crop year (Oct-Sep)
ROTATIONS = {
    "A": {
        "name": "A. Year-round fodder (Field 1 today)",
        "short": "Year-round fodder",
        "plan": [("alfalfa", 10, 1)],
        "why": "What Landsat shows on Field 1 since 2020: green all year, with dips every few weeks "
               "that look like cutting. Good for soil (a legume, always covered) but it pumps water through the summer.",
    },
    "B": {
        "name": "B. Wheat, then pearl millet",
        "short": "Wheat + millet",
        "plan": [("wheat", 12, 1), ("pearl_millet", 6, 1)],
        "why": "Keeps two harvests a year but swaps the long summer fodder for a short, heat-tolerant grain.",
    },
    "C": {
        "name": "C. Wheat, then summer fallow (Field 2 in 2025)",
        "short": "Wheat + fallow",
        "plan": [("wheat", 12, 1), ("fallow", 6, 1)],
        "why": "What Landsat shows on the neighbouring Field 2 in 2025: green from late January to April, bare all summer. "
               "No pumping in the hottest months.",
    },
    "D": {
        "name": "D. Faba bean, then summer fallow",
        "short": "Faba bean + fallow",
        "plan": [("faba_bean", 11, 1), ("fallow", 6, 1)],
        "why": "A short winter legume that adds nitrogen to the soil, then no summer pumping.",
    },
}
