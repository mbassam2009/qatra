"""Crop parameters and the rotations Qatra compares.

Kc and stage lengths: FAO Irrigation and Drainage Paper 56 (Allen et al. 1998),
Table 11 (stage lengths) and Table 12 (single crop coefficients).
  wheat        Kc 0.3 / 1.15 / 0.30   stages 20/50/60/30 (Table 11 row "Calif. Desert, USA", Dec planting,
                                       closest arid-desert analogue; matches Field 2's Landsat green season Dec-Apr)
  berseem      Kc 0.40 / 0.90 / 0.85  (Table 12 "clover hay, Berseem, averaged cutting effects"). Table 11 has no
                                       berseem row, so the stages 15/30/120/16 (Nov 1 to Apr 30) are our assumption
                                       for a winter seasonal fodder, the kind MEWA allows after 16 Nov 2026.
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
    "berseem": {
        "label": "Berseem clover (seasonal fodder)", "kc": (0.40, 0.90, 0.85), "stages": (15, 30, 120, 16),
        "heat_c": 32, "legume": True, "residue": False,
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
        "name": "B. Berseem clover (winter fodder), then summer fallow",
        "short": "Berseem + fallow",
        "plan": [("berseem", 11, 1), ("fallow", 5, 1)],
        "why": "Keeps the farm in fodder with a seasonal crop MEWA allows (licence needed), green November to April, "
               "no summer pumping.",
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


# Perennial (year-round) fodder is banned in Qassim and the other sedimentary-shelf regions from 16 Nov 2026
# (MEWA announcement). Seasonal fodder allowed under licence: Egyptian clover (berseem), Italian and annual ryegrass.
ALLOWED_AFTER_NOV_2026 = {"A": False, "B": True, "C": True, "D": True}

# Crop value per hectare (gross, before costs). Prices in SAR per tonne. Sources:
#  wheat: 6 t/ha average and 1,750 SAR/t MEWA local purchase price, USDA FAS GAIN Grain and Feed Annual, Dec 2025
#  alfalfa: 20.6 t/ha/yr Saudi average (123,837 ha, 2.55 Mt, 2011; Madugundu et al. 2018) and 32 SAR per 15 kg bale
#           retail (USDA FAS GAIN Dec 2025) = 2,133 SAR/t; farm-gate is lower, so this flatters fodder
#  berseem: 11.5 t/ha, the middle of Estidamah's 8-15 t/ha for seasonal winter forage (Arab News, Jan 2026),
#           priced like alfalfa hay
#  faba bean: 4 t/ha, below the 4.9-5.2 t/ha of well-watered KSU trials at Dirab (Migdadi et al. 2016) to allow for
#           farm conditions; 2,700 SAR/t = average 2023 import price (US$723/t, IndexBox), so local beans compete
#           with imports
ECON = {
    "A": {"product": "alfalfa hay", "t_ha": 20.6, "sar_t": 2133},
    "B": {"product": "berseem hay", "t_ha": 11.5, "sar_t": 2133},
    "C": {"product": "wheat grain", "t_ha": 6.0, "sar_t": 1750},
    "D": {"product": "faba beans", "t_ha": 4.0, "sar_t": 2700},
}

# How sure the farmer is of a buyer (1-3, our judgment, shown in the app):
#  wheat 3: the government buys local wheat at a set price (1,750 SAR/t);
#  fodder 2: steady local demand from livestock (berseem needs a seasonal-fodder licence);
#  faba bean 1: no set price, sold against imports.
MARKET = {"A": 2, "B": 2, "C": 3, "D": 1}
