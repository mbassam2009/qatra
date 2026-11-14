"""Qatra web app.  Run:  streamlit run app.py"""
import os

import pandas as pd
import plotly.express as px
import streamlit as st

import model
from config import FIELD, FIELDS

st.set_page_config(page_title="Qatra", layout="wide")
st.title("Qatra: what should this field grow next?")
st.caption(f"{FIELD['name']} · NASA POWER, Landsat, ECOSTRESS · decision support, not a replacement for local advice")

weather = model.load_weather("data/power.csv")
results = model.compare(weather)

tab_map, tab_cond, tab_cmp, tab_pri = st.tabs(["1. Field", "2. Conditions", "3. Compare", "4. Priorities"])

# ---------- 1. Field ----------
with tab_map:
    st.subheader("Two neighbouring fields, same weather")
    st.map(pd.DataFrame([{"lat": f["lat"], "lon": f["lon"]} for f in FIELDS.values()]), zoom=14)
    if os.path.exists("data/ndvi_clean.csv"):
        ndvi = pd.read_csv("data/ndvi_clean.csv", parse_dates=["date"])
        ndvi["field"] = ndvi["field"].map(lambda k: FIELDS.get(k, {}).get("name", k))
        fig = px.line(ndvi.sort_values("date"), x="date", y="ndvi_median", color="field", markers=True,
                      title="Field greenness from Landsat (NDVI). Green in winter = wheat; green in summer = fodder")
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Add data/ndvi_clean.csv (from fetch_landsat_ndvi.js or gee_ndvi.js) to show the field's crop history.")

# ---------- 2. Conditions ----------
with tab_cond:
    st.subheader("Growing conditions")
    m = weather.groupby(weather.index.month).agg(
        et0=("et0", "mean"), tmax=("tmax", "mean"), rain=("rain", "sum"))
    m["rain"] = m["rain"] / weather.index.year.nunique()
    m.index.name = "month"
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(m.reset_index(), x="month", y="et0",
                           labels={"et0": "Reference ET (mm/day)"},
                           title="How thirsty the air is, by month"), width='stretch')
    c2.plotly_chart(px.bar(m.reset_index(), x="month", y="rain",
                           labels={"rain": "Rain (mm/month)"},
                           title="Average monthly rain"), width='stretch')
    st.caption("Groundwater: GRACE satellites show the Saq aquifer losing about 2 km3/yr (2002-2016). "
               "GRACE is regional, so it can't see one field.")

# ---------- 3. Compare ----------
with tab_cmp:
    st.subheader("Crop options for this field")
    cols = st.columns(len(results))
    for col, r in zip(cols, results):
        with col:
            st.markdown(f"### {r['name']}")
            st.metric("Pumped water per year", f"{r['water_m3_ha']:,.0f} m³/ha",
                      help=f"Average over {r['seasons']} seasons, range {r['water_min']:,.0f}-{r['water_max']:,.0f}")
            st.metric("Heat stress days", f"{r['hot_days']:.0f}")
            st.metric("Soil score", f"{r['soil_score']}/4")
            st.write(r["why"])
    st.caption("Checks: a flux tower on a Saudi alfalfa pivot measured about 2,430 mm a year, close to the FAO-56 "
               "number for year-round fodder; ECOSTRESS results are in check_ecostress.py and the web demo (index.html).")

# ---------- 4. Priorities ----------
with tab_pri:
    st.subheader("What matters most to you?")
    w_water = st.slider("Save water", 0, 10, 8)
    w_soil = st.slider("Improve soil", 0, 10, 5)
    w_heat = st.slider("Avoid heat stress", 0, 10, 5)
    df = pd.DataFrame(results)[["name", "water_m3_ha", "hot_days", "soil_score"]]
    norm = lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else s * 0
    df["score"] = (w_water * (1 - norm(df.water_m3_ha))
                   + w_soil * norm(df.soil_score)
                   + w_heat * (1 - norm(df.hot_days)))
    df = df.sort_values("score", ascending=False)
    st.dataframe(df.rename(columns={"water_m3_ha": "water (m³/ha/yr)", "hot_days": "heat days",
                                    "soil_score": "soil (0-4)"}).round(1), hide_index=True)
    st.caption("This is the simple Python version. The web demo (index.html) adds crop value, sure buyer and least change. "
               "Every result needs review by a local agronomist.")
