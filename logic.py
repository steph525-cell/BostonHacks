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


def _txt(v, default="n/a"):
    return default if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "" else str(v)


def match_breakdown(person: dict, place) -> list:
    """Per-preference check for one person vs one place.

    Returns a list of dicts: field, label, wanted, place_value, matched.
    """
    ptype, cuisine = _txt(place.type), _txt(place.cuisine)
    moods = list(place.mood_list) if isinstance(place.mood_list, list) else []
    acts, cuis = person.get("activities") or [], person.get("cuisines") or []
    io, noise = person.get("indoor_outdoor", "Either"), person.get("noise", "Either")
    return [
        dict(field="mood", label="Mood", wanted=person["mood"],
             place_value=", ".join(moods) or "no mood tags", matched=person["mood"] in moods),
        dict(field="activities", label="Want to do", wanted=", ".join(acts) or "anything",
             place_value=ptype, matched=(not acts) or ptype in acts),
        dict(field="cuisines", label="Cuisines", wanted=", ".join(cuis) or "anything",
             place_value=cuisine if ptype == "Food" else f"{ptype} (not a restaurant)",
             matched=(not cuis) or ptype != "Food" or cuisine in cuis),
        dict(field="indoor_outdoor", label="Indoor/Outdoor", wanted=io,
             place_value=_txt(place.indoor_outdoor), matched=io == "Either" or io == place.indoor_outdoor),
        dict(field="noise", label="Noise", wanted=noise,
             place_value=_txt(place.noise), matched=noise == "Either" or noise == place.noise),
    ]


def match_score(person: dict, place) -> float:
    """0–1: share of the 5 preferences this place satisfies."""
    return sum(b["matched"] for b in match_breakdown(person, place)) / 5


WALK_MIN_PER_KM = 12      # walking pace
TRANSFER_MIN = 8          # penalty when you must change lines
MAX_TRIP_MIN = 60         # trips this long score 0 on T convenience


def trip(person, place, st_idx):
    """Estimated T trip for one person to one place."""
    s = st_idx.loc[person["station"]]
    d = st_idx.loc[place.nearest_station]
    ride_km = haversine_km(s.lat, s.lon, d.lat, d.lon)
    walk_km = haversine_km(d.lat, d.lon, place.lat, place.lon)
    direct = person.get("line", "") in str(place.nearest_lines) or person["station"] == place.nearest_station
    minutes = WAIT_MIN + ride_km / T_SPEED_KMH * 60 + walk_km * WALK_MIN_PER_KM + (0 if direct else TRANSFER_MIN)
    return round(minutes), direct, round(walk_km * WALK_MIN_PER_KM)


def recommend(people: list, places: pd.DataFrame, stations: pd.DataFrame,
              open_now=False, top_n=3, transit_weight=0.7):
    """Score = (1 - w) * preference match + w * T convenience.

    T convenience (0-1) = 70% "farthest person's trip is short" + 30% "trips are balanced".
    Trip minutes = wait + ride + walk from station + transfer penalty.
    """
    st_idx = stations.drop_duplicates("station_name").set_index("station_name")
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

    rows = []
    for _, pl in df.iterrows():
        trips, scores = {}, {}
        for p in people:
            trips[p["name"]] = trip(p, pl, st_idx)
            scores[p["name"]] = match_score(p, pl)
        mins = [t[0] for t in trips.values()]
        longest, spread = max(mins), max(mins) - min(mins)
        transit = 0.7 * max(0, 1 - longest / MAX_TRIP_MIN) + 0.3 * max(0, 1 - spread / 30)
        avg_match = sum(scores.values()) / len(scores)
        rows.append({**pl.to_dict(), "avg_match": avg_match, "transit": transit,
                     "longest_min": longest, "spread_min": spread,
                     "total": (1 - transit_weight) * avg_match + transit_weight * transit,
                     "trips": trips, "scores": scores})
    ranked = pd.DataFrame(rows).sort_values("total", ascending=False)
    top = ranked.head(top_n).reset_index(drop=True)
    top["rank"] = range(1, len(top) + 1)
    score_table = pd.DataFrame({r["name"]: r["scores"] for _, r in top.iterrows()}).T
    return top, score_table, None


FIELD_LABEL = {"mood": "Mood", "activities": "Want to do", "cuisines": "Cuisines",
               "indoor_outdoor": "Indoor/Outdoor", "noise": "Noise"}

DEFAULT_ROASTS += [
    "👑 Congrats, {name}! Your taste is so unique, Boston can't keep up.",
    "👑 {name}: the whole Green Line couldn't meet your standards.",
    "👑 Three friends. One impossible main character: {name}.",
    "👑 {name}, your standards have officially caused a service delay.",
    "👑 Even the MBTA can't handle this many preferences, {name}.",
]


def _relaxed(person, field, top):
    """Return (new_value, label) that loosens one SOFT preference.
    Budget and dietary needs are hard constraints and are never relaxed."""
    if field == "mood":
        tags = [m for lst in top["mood_list"] for m in lst]
        best = max(sorted(set(tags)), key=tags.count) if tags else person["mood"]
        return best, best
    if field in ("activities", "cuisines"):
        return [], "anything"
    return "Either", "Either"


def person_match(person, top):
    return sum(match_score(person, r) for _, r in top.iterrows()) / len(top)


def best_compromise(person: dict, top: pd.DataFrame):
    """Try relaxing each soft preference once; return the biggest real improvement.

    Returns dict(field, label, old, new, before, after) or None.
    """
    before = person_match(person, top)
    best = None
    for field in FIELD_LABEL:
        new_val, new_label = _relaxed(person, field, top)
        if new_val == person.get(field):
            continue
        after = person_match({**person, field: new_val}, top)
        if after > before + 1e-9 and (best is None or after > best["after"]):
            old = person.get(field)
            old_txt = ", ".join(old) if isinstance(old, list) and old else (old or "anything")
            best = dict(field=field, label=FIELD_LABEL[field], old=old_txt, new=new_label,
                        before=before, after=after)
    return best


def why_hardest(person: dict, top: pd.DataFrame, places: pd.DataFrame) -> list:
    """Plain-language reasons, computed from the data, for a low match."""
    n = len(top)
    reasons = []
    per_field = {f: [] for f in FIELD_LABEL}
    for _, r in top.iterrows():
        for b in match_breakdown(person, r):
            if not b["matched"]:
                per_field[b["field"]].append(b["place_value"])
    for field, misses in per_field.items():
        if not misses:
            continue
        wanted = next(b["wanted"] for b in match_breakdown(person, top.iloc[0]) if b["field"] == field)
        if field == "mood":
            reasons.append(f"**Mood:** feeling *{wanted}*, but {len(misses)} of {n} picks aren't a *{wanted}* vibe.")
        else:
            got = ", ".join(sorted(set(misses)))
            reasons.append(f"**{FIELD_LABEL[field]}:** wants *{wanted}*, but {len(misses)} of {n} picks are *{got}*.")
    # hard constraints this person adds (counted on the full dataset)
    total = len(places)
    over = int((places["avg_cost"] > person["budget"]).sum())
    if over:
        reasons.append(f"**Budget:** ${person['budget']} rules out {over} of {total} places in our list.")
    for need, col in (("Vegetarian", "vegetarian"), ("Halal", "halal")):
        if need in (person.get("dietary") or []):
            no = int((places[col].astype(str).str.upper() != "Y").sum())
            reasons.append(f"**{need}:** {no} of {total} places can't serve this (we never ask anyone to drop a dietary need).")
    return reasons


def fairness(top_row) -> dict:
    """Longest / shortest trip to one place, and the gap."""
    trips = {name: t[0] for name, t in top_row["trips"].items()}
    longest = max(trips, key=trips.get)
    shortest = min(trips, key=trips.get)
    gap = trips[longest] - trips[shortest]
    if gap <= 5:
        verdict = "Super fair — everyone rides about the same time. 🤝"
    elif gap <= 15:
        verdict = f"Pretty fair — {longest} rides a little longer, but nobody gets stuck crossing the whole city."
    else:
        verdict = f"{longest} is taking one for the team. Buy them a snack. 🍪"
    return dict(longest=longest, longest_min=trips[longest], shortest=shortest,
                shortest_min=trips[shortest], gap=gap, verdict=verdict)


def match_table(score_table: pd.DataFrame) -> pd.DataFrame:
    """Rows = places, columns = friends, values = 0–100 match %."""
    return (score_table * 100).round(0).astype(int)


def hardest_to_please(people: list, score_table: pd.DataFrame, top: pd.DataFrame = None, roasts=None):
    """Who matches the top picks least (lowest average), plus a tip.

    Returns (name, roast_line, tip_line). Winner is computed, never random.
    """
    if score_table is None or len(people) < 2:
        return None, None, None
    avg = score_table.mean(axis=0)
    if avg.max() - avg.min() < 1e-9:
        return None, "🤝 Everyone is equally easy to please. Suspiciously wholesome.", None
    name = avg.idxmin()
    line = random.choice(roasts or DEFAULT_ROASTS).format(name=name)
    if top is None:
        return name, line, None
    person = next(p for p in people if p["name"] == name)
    c = best_compromise(person, top)
    if c:
        tip = (f"💡 Meet halfway: {name}, change **{c['label']}** from *{c['old']}* to *{c['new']}* "
               f"and your match jumps **{c['before']:.0%} → {c['after']:.0%}**.")
    else:
        tip = f"💡 {name}'s picks are already as close as Boston allows — try raising the budget."
    return name, line, tip
