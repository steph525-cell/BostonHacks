"""Scoring logic for the Meet-Halfway app."""
import math
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

MOODS = ["Chill", "Adventurous", "Starving", "Dateish", "Productive"]
ACTIVITIES = ["Food", "Cafe", "Dessert", "Outdoor", "Museum", "Shopping", "Nightlife"]
CUISINES = ["Asian", "American", "Italian", "Mexican", "Middle Eastern", "Other"]
DIETARY = ["Vegetarian", "Halal"]
IO_CHOICES = ["Either", "Indoor", "Outdoor"]
NOISE_CHOICES = ["Either", "Quiet", "Lively"]

DISTANCE_PENALTY = 0.15   # score lost per km of the farthest person's trip
T_SPEED_KMH = 20          # rough average T speed incl. stops
WAIT_MIN = 6              # rough wait + walk overhead

DEFAULT_ROASTS = [
    "🏆 {name} wins Hardest to Please. The group found a place; {name} found a problem.",
    "🏆 {name}, we checked 50 places. You'd still rather stay home.",
    "🏆 Hardest to Please goes to {name}. Next time, you're picking. Good luck.",
    "🏆 {name} wants it cheap, quiet, AND exciting. Pick two.",
    "🏆 {name}: the reason group chats have 47 unread messages.",
    "🏆 Congrats {name}! Your taste is so unique, Boston can't keep up.",
]


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def est_minutes(km):
    return round(WAIT_MIN + km / T_SPEED_KMH * 60)


def _split(v):
    if pd.isna(v) or v == "":
        return []
    return [s.strip() for s in str(v).split("|") if s.strip()]


def prepare_places(places: pd.DataFrame, stations: pd.DataFrame) -> pd.DataFrame:
    """Clean places and auto-compute nearest station."""
    df = places.copy()
    df.columns = [c.strip() for c in df.columns]
    if "verified" in df.columns:
        df = df[df["verified"].astype(str).str.upper().str.strip() == "Y"]
    for c in ["avg_cost", "lat", "lon"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["name", "lat", "lon", "avg_cost"]).reset_index(drop=True)
    df["mood_list"] = df["mood_tags"].apply(_split)
    nearest, lines = [], []
    for _, p in df.iterrows():
        d = stations.apply(lambda s: haversine_km(p.lat, p.lon, s.lat, s.lon), axis=1)
        s = stations.loc[d.idxmin()]
        nearest.append(s.station_name)
        lines.append(s.lines)
    df["nearest_station"] = nearest
    df["nearest_lines"] = lines
    return df


def is_open(open_t, close_t, now=None):
    """True if open now (Boston time). Handles closing after midnight."""
    try:
        now = now or datetime.now(ZoneInfo("America/New_York"))
        t = now.hour * 60 + now.minute
        oh, om = map(int, str(open_t).split(":"))
        ch, cm = map(int, str(close_t).split(":"))
        o, c = oh * 60 + om, ch * 60 + cm
        return o <= t < c if o < c else (t >= o or t < c)
    except Exception:
        return True  # unknown hours: don't hide the place


def match_score(person: dict, place) -> float:
    """0–1: how well one place fits one person's preferences."""
    pts = 0
    pts += person["mood"] in place.mood_list
    pts += (not person["activities"]) or (place.type in person["activities"])
    cuisine_ok = (not person["cuisines"]) or place.type not in ("Food",) \
        or (place.cuisine in person["cuisines"])
    pts += cuisine_ok
    pts += person["indoor_outdoor"] == "Either" or person["indoor_outdoor"] == place.indoor_outdoor
    pts += person["noise"] == "Either" or person["noise"] == place.noise
    return pts / 5


def recommend(people: list, places: pd.DataFrame, stations: pd.DataFrame,
              open_now=False, top_n=3):
    """Return (top places DataFrame, per-person score table, message)."""
    st_idx = stations.set_index("station_name")
    df = places.copy()

    # 1) hard filters
    min_budget = min(p["budget"] for p in people)
    df = df[df["avg_cost"] <= min_budget]
    if any("Vegetarian" in p["dietary"] for p in people):
        df = df[df["vegetarian"].astype(str).str.upper() == "Y"]
    if any("Halal" in p["dietary"] for p in people):
        df = df[df["halal"].astype(str).str.upper() == "Y"]
    if open_now:
        df = df[df.apply(lambda r: is_open(r.open, r.close), axis=1)]
    if df.empty:
        return df, None, ("No place fits everyone 😅 Try raising the lowest budget "
                          f"(${min_budget}) or turning off 'Open now'.")

    # 2) fairness + 3) match
    rows = []
    for _, pl in df.iterrows():
        dists, scores = {}, {}
        for p in people:
            s = st_idx.loc[p["station"]]
            dists[p["name"]] = haversine_km(s.lat, s.lon, pl.lat, pl.lon)
            scores[p["name"]] = match_score(p, pl)
        max_d = max(dists.values())
        avg_match = sum(scores.values()) / len(scores)
        rows.append({**pl.to_dict(), "max_km": max_d, "avg_match": avg_match,
                     "total": avg_match - DISTANCE_PENALTY * max_d,
                     "dists": dists, "scores": scores})
    ranked = pd.DataFrame(rows).sort_values("total", ascending=False)
    top = ranked.head(top_n).reset_index(drop=True)

    score_table = pd.DataFrame({r["name"]: r["scores"] for _, r in top.iterrows()}).T
    return top, score_table, None


def hardest_to_please(people: list, score_table: pd.DataFrame, roasts=None):
    """Person with the lowest average match on the top picks."""
    if score_table is None or len(people) < 2:
        return None, None
    avg = score_table.mean(axis=0)
    name = avg.idxmin()
    if avg.max() - avg.min() < 1e-9:
        return None, "🤝 Wow, everyone is equally easy to please. Suspiciously wholesome."
    line = random.choice(roasts or DEFAULT_ROASTS).format(name=name)
    return name, line
