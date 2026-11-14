# Qatra (قطرة): a water bill for every crop option

NASA Space Apps Challenge 2026 · Challenge: **Field Shift: Adapting Farms with NASA Data** · Local event: Jazan, Saudi Arabia

Qatra shows a farmer in Qassim, Saudi Arabia, how much groundwater each crop rotation would pump on their own center-pivot field. It covers 14 real pivots near Unaizah (2 picked by hand, 12 found automatically in a Sentinel-2 image), shows each one from space every month, and opens with NASA GRACE data on how fast the region's underground water is falling. It reads the field's real crop history from Landsat, runs 11 years of NASA POWER weather through the FAO-56 crop water method, and ranks four rotations by the farmer's own priorities (save water, build soil, avoid heat stress). Every option shows its evidence and what a local expert should check.

**Demo:** open `qatra-demo.html` (or `index.html`) in any browser. No install needed. Click a field on the map.

## Results for two real pivots in Qassim (about 36 km NW of Unaizah)

| Rotation | Pumped water (m³/ha/yr, 10-season average) | Heat-stress days/yr | Soil score (0-4) |
|---|---|---|---|
| A. Year-round fodder (what Landsat shows on Field 1 since 2020) | 30,078 (28,492 to 30,998) | 126 | 3 |
| B. Wheat, then pearl millet | 18,355 | 120 | 2 |
| C. Wheat, then summer fallow (what Field 2 did in 2025) | 8,378 | 35 | 1 |
| D. Faba bean, then summer fallow | 3,605 | 8 | 2 |

Field 1 is 33.4 ha: switching from A to C would pump about **725,000 m³ less per year** by FAO-56, or about **270,000 m³** if ECOSTRESS is right (see the check below).
Reference ET at the fields averages 2,547 mm/yr against 80 mm/yr of rain (NASA POWER, 2015-2025).

## Regional context (GRACE)

NASA GRACE/GRACE-FO (JPL mascon CRI, via NASA GIBS) over 25-28 N, 42-45 E: water storage fell from about +4 cm (2003) to -17.7 cm (mid-2022) against the 2004-2009 average, a trend of -1.2 cm a year, about 22 km³ lost under this 3° × 3° area (`fetch_grace_gibs.py`, `data/grace_qassim.csv`).

## All 14 fields (`fields.py`, `data/fields.json`)

Each field's 2024-25 water use is estimated from its own monthly Landsat greenness (cover × ET0, minus effective rain, ÷ 0.8). The 14 fields pumped about 5.5 million m³ in 2024-25 by this FAO-56-style estimate, or about 2.0 million m³ scaled to ECOSTRESS. Field 1 (33.4 ha, green all year) pumped about 949,000 m³; Field 2 (19.6 ha, winter crop only) about 142,000 m³.

## How it works

1. **Data in:** NASA POWER daily weather (Tmax, Tmin, RH, wind at 2 m, solar radiation, rain), 2015-2025, at 26.296 N, 43.723 E. Landsat 8/9 Collection 2 Level-2 surface reflectance, 299 scenes, via Microsoft Planetary Computer.
2. **Prepare:** FAO-56 Penman-Monteith reference ET (`et0.py`, checked against FAO-56 Example 18: 3.88 vs 3.9 mm/day). Field greenness (NDVI) averaged over a ring inside each pivot (skipping the bare pivot point and the edge); cloudy passes removed by blue reflectance.
3. **Build:** for each day of each crop year, crop ET = Kc × ET0 (FAO-56 Tables 11-12), minus effective rain, divided by 80% pivot efficiency. Heat-stress days = days above each crop's rough heat limit. Simple soil score: legume (+2), soil covered 8+ months (+1), cereal stubble (+1).
4. **Result:** four rotations ranked by the farmer's sliders, with whole-field totals and the change vs today.

## Run it

    pip install -r requirements.txt
    python fetch_power.py          # NASA POWER weather -> data/power.csv (already included)
    python fetch_landsat_ndvi.py   # Landsat NDVI for both fields -> data/ndvi_clean.csv (already included)
    python model.py                # prints the results table
    streamlit run app.py           # optional Python version of the app

## Files

- `config.py`: the two fields (centre, radius), years, pivot efficiency
- `et0.py`: FAO-56 Penman-Monteith reference ET
- `crops.py`: crop coefficients, stage lengths, heat limits and the four rotations, with sources
- `model.py`: water, heat and soil results per rotation
- `fetch_power.py`, `fetch_landsat_ndvi.py`, `gee_ndvi.js`: data download scripts
- `check_ecostress.py`: compares ECOSTRESS daily ET with reference ET and Landsat crop state
- `fields.py`: classifies all 14 fields from Landsat and estimates their 2024-25 water use
- `fetch_grace_gibs.py`: GRACE/GRACE-FO water storage for the Qassim area from NASA GIBS
- `app.py`: Streamlit app; `qatra-demo.html`: the standalone web demo
- `data/`: power.csv, ndvi_raw.csv, ndvi_clean.csv (14 fields), elev.txt, ecostress_jet_raw.csv, ecostress_check.csv, grace_qassim.csv, fields.json

## Next steps

1. Ask MEWA for meter readings from a few farm wells (Hafiz platform) to see whether FAO-56 or ECOSTRESS is closer.
2. Compare our numbers with the KAUST satellite study of 35,000 Saudi pivots.
3. An Arabic version that works on a phone, tested with 3 to 5 farmers near Unaizah.
4. Cover every pivot in Qassim, use GRACE-FO up to 2026, and add crop prices.

## Limits

- Crop water follows FAO-56 coefficients for the closest arid regions, not field measurements in Qassim.
- Pivot efficiency is assumed at 80%. Heat limits are rough thresholds. Income is not scored.
- The crop on Field 1 (alfalfa or Rhodes grass) is inferred from Landsat, not confirmed on the ground.
- ECOSTRESS check (`check_ecostress.py`, 438 readings of ECO_L3T_JET.002 daily ET at 8 points, 2019-2025, via AppEEARS): ECOSTRESS follows crop state (median ET/ET0 0.10 on bare, 0.22 partly green, 0.35 green; correlation 0.64 with Landsat NDVI), but on green fields it measures about a third of what FAO-56 assumes (Kc 0.95-1.15). We treat FAO-56 as the upper estimate and ECOSTRESS (x0.37) as the lower one. AppEEARS labels ETdaily as W/m², but the values (0-8.5) only make sense as mm/day, so we read them as mm/day. Morning overpasses read lower than afternoon ones, a sign the daily upscaling adds uncertainty.

## NASA data and references

- NASA POWER daily data: https://power.larc.nasa.gov/
- Landsat 8/9 Collection 2 Level-2 (NASA/USGS), via Microsoft Planetary Computer: https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2
- GRACE result for the Saq aquifer (about -2 km³/yr, 2002-2016; ~88% of use is irrigation): Arabian Journal for Science and Engineering, 2019, https://link.springer.com/article/10.1007/s13369-019-04069-1
- Allen et al. 1998, FAO Irrigation and Drainage Paper 56 (Crop evapotranspiration): https://www.fao.org/4/x0490e/x0490e0b.htm (Chapter 6, Tables 11-12)
- KAUST, satellite monitoring of groundwater use by center pivots (prior work): https://discovery.kaust.edu.sa/en/article/6446/monitoring-precious-groundwater-resources-for-arid-agricultural-regions/
- ECOSTRESS ECO_L3T_JET.002 (Hook & Halverson 2024): https://doi.org/10.5067/ECOSTRESS/ECO_L3T_JET.002, accessed through NASA AppEEARS v3.137
- GRACE/GRACE-FO JPL mascon CRI RL06.3 (PO.DAAC), served by NASA GIBS layer GRACE_Tellus_Liquid_Water_Equivalent_Thickness_Mascon_CRI: https://podaac.jpl.nasa.gov/dataset/TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4
- Copernicus Sentinel-2 L2A (ESA), via Microsoft Planetary Computer, for the map, monthly images and pivot detection
- Saudi green fodder cultivation ban, Nov 2018: https://www.argaam.com/en/article/articledetail/id/568056
- AI: Claude (Anthropic) was used for research, coding and design help (see the project page).
