import os

import pandas as pd
import pydeck as pdk
import streamlit as st

import logic as L

st.set_page_config(page_title="Meet Me Halfway", page_icon="🚇", layout="wide")


# ---------- data ----------
@st.cache_data
def load_data():
    st_path = "data/stations.csv" if os.path.exists("data/stations.csv") else "data/stations_sample.csv"
    pl_path = "data/places.csv" if os.path.exists("data/places.csv") else "data/places_sample.csv"
    stations = pd.read_csv(st_path)
    places = L.prepare_places(pd.read_csv(pl_path), stations)
    return stations, places, pl_path


def load_roasts():
    if os.path.exists("assets/roasts.txt"):
        with open("assets/roasts.txt", encoding="utf-8") as f:
            lines = [l.strip() for l in f if "{name}" in l]
        if lines:
            return lines
    return None


stations, places, pl_path = load_data()
STATION_NAMES = sorted(stations["station_name"].tolist())

DEMO = [
    dict(name="Stephanie", line="Green", station="Boston University Central", budget=20, mood="Starving",
         activities=["Food"], cuisines=["Asian"], dietary=[], indoor_outdoor="Indoor", noise="Either"),
    dict(name="Alex", line="Red", station="Harvard", budget=15, mood="Chill",
         activities=["Food", "Cafe"], cuisines=["Asian", "Mexican"], dietary=["Vegetarian"],
         indoor_outdoor="Either", noise="Either"),
    dict(name="Jordan", line="Green", station="Northeastern University", budget=25, mood="Dateish",
         activities=["Museum", "Dessert"], cuisines=["Italian"], dietary=[],
         indoor_outdoor="Outdoor", noise="Quiet"),
]


LINES = ["Red", "Orange", "Blue", "Green"]


def stations_on(line):
    names = stations[stations["lines"].astype(str).str.contains(line)]["station_name"]
    return sorted(names.tolist()) or STATION_NAMES


def set_person(i, p):
    p = dict(p)
    if p["station"] not in STATION_NAMES:
        p["station"] = STATION_NAMES[0]
    if p.get("line") not in LINES or p["station"] not in stations_on(p["line"]):
        row_lines = str(stations.set_index("station_name").loc[p["station"], "lines"])
        p["line"] = next((l for l in LINES if l in row_lines), "Green")
    for k, v in p.items():
        st.session_state[f"{k}_{i}"] = v


# ---------- header ----------
st.title("🚇 Meet Me Halfway")
st.caption("Find a fair spot on the T for everyone — and find out who's the hardest to please.")
if "sample" in pl_path:
    st.info("Using SAMPLE data. Put the real file at data/places.csv to switch.")

# ---------- inputs ----------
c1, c2 = st.columns([1, 3])
with c1:
    if st.button("🎲 Load demo group", use_container_width=True):
        st.session_state["n_people"] = len(DEMO)
        for i, p in enumerate(DEMO):
            set_person(i, p)
    st.session_state.setdefault("n_people", 3)
    n = st.number_input("How many people?", 2, 5, key="n_people")
    open_now = st.toggle("Open now only", value=False)

people = []
cols = st.columns(int(n))
for i, col in enumerate(cols):
    st.session_state.setdefault(f"name_{i}", f"Friend {i+1}")
    st.session_state.setdefault(f"budget_{i}", 20)
    with col:
        with st.container(border=True):
            name = st.text_input("Name", key=f"name_{i}")
            line = st.selectbox("T line", LINES, key=f"line_{i}")
            options = stations_on(line)
            if st.session_state.get(f"station_{i}") not in options:
                st.session_state[f"station_{i}"] = options[0]
            station = st.selectbox("Starting T stop", options, key=f"station_{i}")
            budget = st.slider("Budget ($/person)", 0, 60, key=f"budget_{i}")
            mood = st.selectbox("Mood", L.MOODS, key=f"mood_{i}")
            activities = st.multiselect("Want to do", L.ACTIVITIES, key=f"activities_{i}")
            cuisines = st.multiselect("Cuisines", L.CUISINES, key=f"cuisines_{i}")
            dietary = st.multiselect("Dietary", L.DIETARY, key=f"dietary_{i}")
            io = st.radio("Indoor / Outdoor", L.IO_CHOICES, key=f"indoor_outdoor_{i}", horizontal=True)
            noise = st.radio("Noise", L.NOISE_CHOICES, key=f"noise_{i}", horizontal=True)
            people.append(dict(name=name or f"Friend {i+1}", line=line, station=station, budget=budget,
                               mood=mood, activities=activities, cuisines=cuisines,
                               dietary=dietary, indoor_outdoor=io, noise=noise))

go = st.button("✨ Find our spot", type="primary", use_container_width=True)

# ---------- results ----------
if go:
    top, scores, msg = L.recommend(people, places, stations, open_now=open_now)
    if msg:
        st.warning(msg)
        st.stop()

    st.subheader("🏁 Top picks")
    rc = st.columns(len(top))
    for col, (_, r) in zip(rc, top.iterrows()):
        with col:
            with st.container(border=True):
                st.markdown(f"### {r['name']}")
                st.write(f"{r['type']} · ${r['avg_cost']:.0f}/person · {r['noise']} · {r['indoor_outdoor']}")
                st.write(f"🚉 Nearest T: **{r['nearest_station']}** ({r['nearest_lines']})")
                st.write(f"🕒 {r['open']}–{r['close']}")
                st.progress(min(max(r["avg_match"], 0), 1.0), text=f"Group match {r['avg_match']:.0%}")
                for p in people:
                    km = r["dists"][p["name"]]
                    st.caption(f"{p['name']}: ~{L.est_minutes(km)} min from {p['station']} ({p['line']} Line, est.)")

    # map
    st_idx = stations.set_index("station_name")
    pts = [dict(label=f"{p['name']} ({p['station']})", lat=st_idx.loc[p["station"]].lat,
                lon=st_idx.loc[p["station"]].lon, color=[30, 120, 255]) for p in people]
    pts += [dict(label=f"#{i+1} {r['name']}", lat=r["lat"], lon=r["lon"], color=[255, 80, 60])
            for i, (_, r) in enumerate(top.iterrows())]
    mdf = pd.DataFrame(pts)
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(latitude=mdf.lat.mean(), longitude=mdf.lon.mean(), zoom=12.5),
        layers=[pdk.Layer("ScatterplotLayer", mdf, get_position="[lon, lat]",
                          get_fill_color="color", get_radius=120, pickable=True)],
        tooltip={"text": "{label}"},
    ))
    st.caption("🔵 friends' starting stops · 🔴 top picks")

    # hardest to please
    who, line = L.hardest_to_please(people, scores, load_roasts())
    if line:
        st.subheader("😈 Hardest to Please")
        st.success(line)
        if who:
            st.balloons()
        with st.expander("See everyone's match scores"):
            st.dataframe((scores * 100).round(0).astype(int).astype(str) + "%")
