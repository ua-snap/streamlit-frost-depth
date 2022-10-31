import streamlit as st
from modberg import *

st.title("MODIFIED BERGGREN FROST DEPTH CALCULATOR")
st.subheader("Alaska Climate Change Edition")

st.subheader("Select a location:")
col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("latitude in Alaska", 51.229, 71.3526, 65.0)
with col2:
    lon = st.number_input("longitude in Alaska", -179.1506, -129.9795, -147.0)

st.subheader("Retrieve the mean annual temperature (°F) from the SNAP Data API")
model = st.radio(
    "climate model for the projected mean annual temperature",
    ("GFDL-CM3", "NCAR-CCSM4", "GISS-E2-R", "IPSL-CM5A-LR", "MRI-CGCM3"))
scenario = st.radio(
    "RCP emissions scenario for the projected mean annual temperature",
    ("rcp45", "rcp6", "rcp85"))
year_start, year_end = st.slider(
    'Select range for mean annual temperature summary',
    2007, 2100, (2040, 2069))

mat = get_projected_mat_from_api(
    lat, lon, model, scenario, year_start, year_end)
mat_str = f"Mean Annual Temperature: {mat}°F"
st.subheader(mat_str)

st.subheader(
    "Retrieve the RCP 8.5 design freezing index (°F days) from the SNAP Data API")
model = st.radio(
    "climate model for the design freezing index (only two are available)",
    ("GFDL-CM3", "NCAR-CCSM4"))
era = st.radio(
    "summary era for the design freezing index",
    ("2040-2069", "2070-2099"))

FI = get_projected_design_fi_from_api(lat, lon, model, era)
fi_str = f"Design Freezing Index: {FI} °F days"
st.subheader(fi_str)


col1, col2 = st.columns(2)
with col1:
    st.header("CLIMATE PARAMETERS")
    n = st.slider(
        "n factor converting air to surface freezing index", 0.1, 1.0, 0.75)
    d = st.slider("length of freezing duration (days)", 30, 300, 160)
    nFI = n * FI
    # I've seen a few references where the ground temperature used in thermal ratio computation is assumed to equal the mean annual air temperature. I don't know if that is a common practice, but to be simple that is what I've done here. We could pull a ground temperature (but at what depth?) from the API if we needed to.
    magt = mat

with col2:
    st.header("SOIL PARAMETERS")
    wc_pct = st.slider("water content (percent)", 1, 50, 15)
    dry_ro = st.slider("dry unit weight (pounds per cubic foot)", 20, 135, 100)
    k_avg = st.slider(
        "average thermal conductivity (BTU/(ft•hr•°F))",
        0.01,
        2.0,
        0.78,
    )

mb = compute_modified_bergrenn(
    dry_ro,
    wc_pct,
    mat,
    magt,
    d,
    nFI,
    k_avg,
    lat, lon, model, scenario, year_start, year_end
)

st.success(f"COMPUTED FROST DEPTH (FT.): {mb}")
