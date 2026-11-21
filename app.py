"""Meet Me Halfway — BostonHacks 2026 (Streamlit UI).

Flow: Step 1 Where? → Step 2 Vibe → Results page 1 (meeting point) → Results page 2 (hardest to please).
All inputs live in st.session_state so switching pages never loses them.
"""
import html
import json
import os
import random

import pandas as pd
import pydeck as pdk
import streamlit as st

import logic as L

st.set_page_config(page_title="Meet Me Halfway", page_icon="🚇", layout="wide")

MAX_PEOPLE = 5
LINES = ["Red", "Orange", "Blue", "Green"]
LINE_HEX = {"Red": "#D21F36", "Orange": "#F2A323", "Blue": "#3575DE", "Green": "#218447"}
LINE_RGB = {"Red": [210, 31, 54], "Orange": [242, 163, 35], "Blue": [53, 117, 222], "Green": [33, 132, 71]}
TYPE_ICON = {"Food": "🍜", "Cafe": "☕", "Dessert": "🍰", "Outdoor": "🌳",
             "Museum": "🖼️", "Shopping": "🛍️", "Nightlife": "🎤"}
INPUT_FIELDS = ["name", "line", "station", "budget", "mood", "activities", "cuisines",
                "dietary", "indoor_outdoor", "noise"]

# ---------------------------------------------------------------- styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&display=swap');
.stApp {
  background-color: #FFFFFF;
  background-image: linear-gradient(#D6ECF7 1px, transparent 1px),
                    linear-gradient(90deg, #D6ECF7 1px, transparent 1px);
  background-size: 26px 26px;
}
h1, h2, h3, .mmh-title, .mmh-h, .mmh-big { font-family: 'Fredoka', sans-serif !important; color: #111; }
.mmh-title { font-size: 3rem; font-weight: 700; line-height: 1.05; margin: 0; }
.mmh-tag { font-size: 1.15rem; font-weight: 600; margin: .2rem 0 1rem 0; }
.mmh-h { display: inline-block; background: #F7E000; border: 3px solid #111; border-radius: 14px;
  padding: 4px 16px; box-shadow: 4px 4px 0 #111; font-size: 1.45rem; font-weight: 700; margin: 10px 0 14px 0; }
.mmh-card { background: #FFFFFF; border: 3px solid #111; border-radius: 18px; box-shadow: 5px 5px 0 #111;
  padding: 16px 20px; margin-bottom: 16px; color: #111; }
.mmh-blue { background: #EAF6FC; }
.mmh-hot { background: #FFE3E8; border-color: #111; }
.mmh-big { font-size: 1.9rem; font-weight: 700; line-height: 1.1; }
.mmh-pill { display: inline-block; padding: 2px 10px; border-radius: 999px; color: #fff; font-weight: 700;
  font-size: .85rem; margin-right: 4px; border: 2px solid #111; }
.mmh-chip { display: inline-block; padding: 2px 10px; border-radius: 999px; background: #F7E000; color: #111;
  font-weight: 700; font-size: .85rem; margin: 2px 4px 2px 0; border: 2px solid #111; }
.mmh-step { display: inline-block; padding: 6px 16px; border-radius: 999px; border: 3px solid #111;
  font-family: 'Fredoka', sans-serif; font-weight: 600; margin-right: 8px; background: #fff; color: #111; }
.mmh-step.on { background: #F7E000; box-shadow: 3px 3px 0 #111; }
.mmh-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0;
  border-bottom: 2px dashed #BBD9EA; gap: 10px; flex-wrap: wrap; }
.mmh-row:last-child { border-bottom: none; }
.mmh-bar { height: 12px; border: 2px solid #111; border-radius: 999px; background: #fff; overflow: hidden; margin: 4px 0 10px 0; }
.mmh-bar > div { height: 100%; }
table.mmh-t { border-collapse: separate; border-spacing: 0; width: 100%; border: 3px solid #111;
  border-radius: 14px; overflow: hidden; background: #fff; color: #111; }
table.mmh-t th, table.mmh-t td { padding: 9px 12px; border-bottom: 2px solid #111; text-align: center; }
table.mmh-t th { background: #F7E000; font-family: 'Fredoka', sans-serif; }
table.mmh-t td:first-child, table.mmh-t th:first-child { text-align: left; font-weight: 700; }
table.mmh-t tr:last-child td { border-bottom: none; }
.stButton > button { border: 3px solid #111 !important; border-radius: 999px !important;
  box-shadow: 3px 3px 0 #111; font-weight: 700; }
.stButton > button[kind="primary"] { background: #D21F36 !important; color: #fff !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { background: #fff; border: 3px solid #111 !important;
  border-radius: 18px !important; box-shadow: 4px 4px 0 #111; }

.mmh-brand { font-family:'Fredoka',sans-serif; font-weight:700; letter-spacing:1px; font-size:1rem; }
.mmh-hero { display:inline-block; background:#F7E000; border:4px solid #111; border-radius:22px; padding:10px 28px;
  box-shadow:6px 6px 0 #111; transform:rotate(-2deg); font-family:'Fredoka',sans-serif; font-weight:700;
  font-size:3.2rem; line-height:1; color:#111; margin:6px 0 8px 0; }
.mmh-stepper { display:flex; align-items:center; gap:0; margin:14px 0 18px 0; max-width:560px; }
.mmh-stepper .s { display:flex; flex-direction:column; align-items:center; font-family:'Fredoka',sans-serif; font-weight:600; min-width:70px; }
.mmh-stepper .dot { width:38px; height:38px; border-radius:50%; border:3px solid #111; display:flex; align-items:center;
  justify-content:center; font-weight:700; background:#fff; }
.mmh-stepper .dot.done { background:#218447; color:#fff; }
.mmh-stepper .dot.on { background:#F7E000; box-shadow:3px 3px 0 #111; }
.mmh-stepper .ln { flex:1; height:4px; background:#111; margin:0 4px 22px 4px; border-radius:4px; }
.mmh-head { background:#fff; border:3px solid #111; border-radius:22px; box-shadow:5px 5px 0 #111; padding:14px 22px;
  margin-bottom:16px; text-align:center; }
.mmh-head .t { font-family:'Fredoka',sans-serif; font-weight:700; font-size:2rem; color:#111; }
.mmh-head .t span { background:#F7E000; padding:0 10px; border-radius:10px; }
.mmh-head .sub { color:#333; margin-top:2px; }
.mmh-friend { display:flex; align-items:center; gap:14px; background:#fff; border:3px solid #111; border-radius:16px;
  box-shadow:4px 4px 0 #111; padding:10px 16px; margin-bottom:12px; }
.mmh-friend .av { font-size:2.2rem; }
.mmh-friend .nm { font-family:'Fredoka',sans-serif; font-weight:700; font-size:1.25rem; }
.mmh-toppick { position:relative; background:#fff; border:4px solid #111; border-radius:20px; box-shadow:6px 6px 0 #F7E000, 9px 9px 0 #111;
  padding:18px 20px; margin:14px 0 18px 0; display:flex; gap:18px; align-items:center; color:#111; }
.mmh-toppick .tag { position:absolute; top:-16px; left:22px; background:#F7E000; border:3px solid #111; border-radius:10px;
  padding:1px 12px; font-family:'Fredoka',sans-serif; font-weight:700; }
.mmh-illo { min-width:130px; height:130px; border:3px solid #111; border-radius:16px; background:#EAF6FC;
  display:flex; align-items:center; justify-content:center; font-size:4rem; }
.mmh-bubble { background:#FFD6DE; border:3px solid #111; border-radius:50%; width:120px; height:120px; display:flex;
  flex-direction:column; align-items:center; justify-content:center; font-family:'Fredoka',sans-serif; font-weight:700; flex-shrink:0; }
.mmh-bubble b { font-size:1.9rem; }
.mmh-badge { display:inline-block; padding:1px 10px; border-radius:8px; border:2px solid #111; font-weight:700; font-size:.85rem; }
.mmh-badge.ok { background:#CDEFD8; color:#145c2f; } .mmh-badge.tr { background:#FFE2B8; color:#8a4b00; }
.mmh-banner { background:#D21F36; color:#fff; border:4px solid #111; border-radius:22px; box-shadow:6px 6px 0 #111;
  padding:22px 26px; margin:10px 0 18px 0; display:flex; align-items:center; justify-content:space-between; gap:16px; }
.mmh-banner .c { font-family:'Fredoka',sans-serif; font-weight:700; font-size:2.6rem; line-height:1.05; }
.mmh-banner .c span { background:#F7E000; color:#111; padding:0 12px; border-radius:12px; }
.mmh-banner .r { font-family:'Fredoka',sans-serif; font-weight:600; font-size:1.4rem; margin-top:6px; }
.mmh-hl { font-family:'Fredoka',sans-serif; background:#F7E000; padding:0 8px; border-radius:6px; font-weight:700; }
.mmh-strip { background:#FFE3E8; border:2px solid #111; border-radius:12px; padding:8px 14px; margin-bottom:16px; }
.mmh-pchip { display:inline-block; border:2px solid #111; border-radius:999px; padding:3px 12px; margin:4px 6px 4px 0; font-weight:600; background:#fff; }
.mmh-pchip.miss { background:#FFD6DE; } .mmh-pchip.hit { background:#CDEFD8; }
.mmh-formula { background:#CDEFD8; border:2px solid #111; border-radius:10px; padding:6px 12px; font-weight:700; text-align:center; margin:8px 0; }
.stButton > button[kind="primary"] { background:#F7E000 !important; color:#111 !important; font-family:'Fredoka',sans-serif;
  font-size:1.25rem !important; padding:.55rem 1rem !important; }
div[data-testid="stButtonGroup"] button { border:2px solid #111 !important; color:#111 !important; }
div[data-testid="stButtonGroup"] button[data-selected="true"],
div[data-testid="stButtonGroup"] button[aria-pressed="true"],
div[data-testid="stButtonGroup"] button[aria-checked="true"] { background:#F7E000 !important; font-weight:700; box-shadow:2px 2px 0 #111; }
div[data-testid="stButtonGroup"] button[data-selected="true"] *, div[data-testid="stButtonGroup"] button[aria-pressed="true"] *,
div[data-testid="stButtonGroup"] button[aria-checked="true"] * { color:#111 !important; }

/* BostonHacks key-visual details: ruled notebook, subway ribbons, comic stickers */
.block-container { max-width: 1330px; padding-top: 1.35rem; padding-bottom: 4rem; }
.stApp [data-testid="stHeader"] { background: transparent; }
.stApp p, .stApp label { color: #111111; }
.mmh-brand { display: inline-block; padding: 4px 13px; background:#fff;
  border:2px solid #111; border-radius:999px; transform:rotate(-1deg); margin-bottom:8px; }
.mmh-hero { position:relative; max-width:100%; overflow-wrap:anywhere; }
.mmh-hero::after { content:"✦"; font-size:2rem; color:#D21F36;
  position:absolute; right:-18px; top:-27px; transform:rotate(20deg); }
.mmh-route-art { position: relative; height: 50px; overflow:hidden; margin: 4px 0 16px; }
.mmh-route-art .track { position:absolute; left:0; right:0; height:8px;
  border-radius:999px; border:2px solid #111; }
.mmh-route-art .green { top:9px; background:#218447; transform:rotate(-1.2deg); }
.mmh-route-art .red { top:28px; background:#D21F36; transform:rotate(1.4deg); }
.mmh-route-art .stop { position:absolute; top:10px; left:46%; width:30px; height:30px;
  border:5px solid #111; background:#F7E000; border-radius:50%; z-index:2; }
.mmh-banner { position: relative; background:#D21F36; isolation:isolate;
  background-image:radial-gradient(circle at 10% 17%,#ffffff30 0 3px,transparent 4px),
    radial-gradient(circle at 84% 72%,#ffffff30 0 4px,transparent 5px); }
.mmh-banner::before {content:"✦"; position:absolute; top:-28px; left:-15px;
  font-size:3.1rem; color:#F7E000; -webkit-text-stroke:2px #111; transform:rotate(-18deg); }
.mmh-banner::after {content:"✦ ✦"; position:absolute; right:8px; bottom:-25px;
  color:#F7E000; font-size:2.4rem; -webkit-text-stroke:1px #111; transform:rotate(12deg); }
.mmh-banner .roast { background: #fff; color:#111; display:inline-block;
  padding:9px 14px; border:3px solid #111; border-radius:16px; box-shadow:4px 4px 0 #F7E000;
  transform:rotate(-1deg); margin: 14px 0 4px; font-size:1.13rem; font-weight:700; }
.mmh-sticker { display:inline-block; background:#F7E000; color:#111; border:3px solid #111;
  border-radius:12px; padding:4px 12px; font-family:'Fredoka',sans-serif;
  font-size:1rem; transform:rotate(-3deg); box-shadow:3px 3px 0 #111; }
.mmh-split-title { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin:8px 0 18px; }
.mmh-disclaimer { display:block; font-size:.78rem; padding-top:8px; color:#3f4e57; }
.mmh-friend { border-left-width:10px; }
.mmh-person-mini { border:2px solid #111; border-radius:12px; background:#fff;
  padding:7px 12px; display:inline-block; margin:0 8px 8px 0; font-weight:600; }
@media (max-width: 760px) {
 .block-container { padding-left:.8rem; padding-right:.8rem; }
 .mmh-hero { font-size:2.05rem; padding:9px 16px; }
 .mmh-head .t { font-size:1.5rem; }
 .mmh-toppick { flex-direction:column; align-items:stretch; padding:21px 13px 12px; }
 .mmh-illo { min-width:0; width:100%; height:90px; }
 .mmh-bubble { width:100%; height:auto; border-radius:12px; padding:8px; }
 .mmh-banner { flex-direction:column-reverse; align-items:flex-start; padding:19px 14px; }
 .mmh-banner .c { font-size:2rem; }
 .mmh-banner .r { font-size:1.1rem; }
 .mmh-h { font-size:1.1rem; }
 .mmh-stepper .s { min-width:52px; }
 .mmh-stepper .dot { width:32px; height:32px; }
 .mmh-card { padding:13px; }
 .mmh-t th,.mmh-t td { padding:5px 4px !important; font-size:.72rem; }
}


/* ---- force readable dark text even when the phone is in dark mode ---- */
.stApp { color-scheme: light; color:#111111; }
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stWidgetLabel"] p,
.stApp label, .stApp summary, .stApp summary p, .stApp [data-testid="stExpander"] p { color:#111111 !important; }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p { color:#333333 !important; }
.mmh-tag, .mmh-brand, .mmh-stepper .s, .mmh-hl, .mmh-sticker, .mmh-head .t { color:#111111 !important; }
.mmh-head .sub { color:#222222 !important; }
.stApp input, .stApp textarea, .stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"],
.stApp [data-testid="stNumberInput"] div, .stApp [data-testid="stNumberInput"] button {
  background:#FFFFFF !important; color:#111111 !important; }
.stApp [data-testid="stExpander"] details, .stApp [data-testid="stExpander"] summary { background:#FFFFFF !important; }
.stButton > button, [data-testid="stPopover"] button { background:#FFFFFF !important; color:#111111 !important; }
.stButton > button p, [data-testid="stPopover"] button p { color:#111111 !important; }
div[data-testid="stButtonGroup"] button { background:#FFFFFF !important; }
div[data-testid="stButtonGroup"] button p { color:#111111 !important; }
.mmh-banner .c, .mmh-banner > div > div:not(.roast):not(.mmh-sticker) { color:#FFFFFF !important; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display:none !important; }
div[data-testid="stButtonGroup"], div[data-testid="stButtonGroup"] > div, div[data-testid="stButtonGroup"] div[role="radiogroup"] { flex-wrap:wrap !important; overflow:visible !important; row-gap:6px; }
/* friend icon: colored circle with initial (no skin tones) */
.mmh-av { display:inline-flex; align-items:center; justify-content:center; width:38px; height:38px; border-radius:50%;
  border:3px solid #111; color:#fff !important; font-family:'Fredoka',sans-serif; font-weight:700; font-size:1.1rem;
  vertical-align:middle; flex-shrink:0; }
.mmh-av.sm { width:26px; height:26px; font-size:.8rem; border-width:2px; margin-right:4px; }
.mmh-mystery { background:#111; color:#F7E000 !important; border:4px solid #111; border-radius:22px; box-shadow:6px 6px 0 #F7E000;
  padding:22px; text-align:center; margin:6px 0 16px 0; }
.mmh-mystery .q { font-family:'Fredoka',sans-serif; font-size:3.4rem; font-weight:700; letter-spacing:6px; color:#F7E000 !important; }
.stApp [data-testid="stMarkdownContainer"] .mmh-mystery p, .mmh-mystery p { color:#FFFFFF !important; margin:4px 0 0 0; }
.mmh-mystery .ppl { margin-top:12px; }
.mmh-mystery .ppl .mmh-av { margin:0 4px; }
.mmh-toppick .mmh-bubble { order:-1; }
@media (max-width: 760px) {
 .mmh-toppick .mmh-bubble { width:100%; height:auto; border-radius:14px; padding:10px; flex-direction:row; gap:12px; }
 .mmh-mystery .q { font-size:2.4rem; }
}
</style>
""", unsafe_allow_html=True)


def h(text):
    st.markdown(f'<div class="mmh-h">{text}</div>', unsafe_allow_html=True)


def esc(x):
    return html.escape(str(x))


def line_pill(line):
    return f'<span class="mmh-pill" style="background:{LINE_HEX.get(line, "#111")}">{esc(line)}</span>'


def lines_pills(lines_str):
    return "".join(line_pill(l) for l in str(lines_str).split("|") if l)


def md(text):
    """Tiny **bold** / *italic* converter for reason strings (after escaping)."""
    import re
    t = esc(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)


def bar(value, color):
    pct = max(0, min(100, round(value * 100)))
    return f'<div class="mmh-bar"><div style="width:{pct}%;background:{color}"></div></div>'


# ---------------------------------------------------------------- data
@st.cache_data
def load_data():
    st_path = "data/stations.csv" if os.path.exists("data/stations.csv") else "data/stations_sample.csv"
    pl_path = "data/places.csv" if os.path.exists("data/places.csv") else "data/places_sample.csv"
    stations = pd.read_csv(st_path).dropna(subset=["station_name", "lat", "lon"])
    stations["lines"] = stations["lines"].fillna("").astype(str)
    places = L.prepare_places(pd.read_csv(pl_path), stations)
    return stations, places, pl_path


def load_roasts():
    if os.path.exists("assets/roasts.txt"):
        with open("assets/roasts.txt", encoding="utf-8") as f:
            lines = [l.strip() for l in f if "{name}" in l]
        if lines:
            return lines
    return L.DEFAULT_ROASTS


stations, places, pl_path = load_data()
STATION_NAMES = sorted(stations["station_name"].unique().tolist())


def stations_on(line):
    names = stations[stations["lines"].str.contains(line)]["station_name"].unique().tolist()
    return sorted(names) or STATION_NAMES


def line_of(station):
    row = stations[stations["station_name"] == station]
    lines = str(row["lines"].iloc[0]) if len(row) else ""
    return next((l for l in LINES if l in lines), "Green")


# ---------------------------------------------------------------- state
ss = st.session_state

# keep widget values alive when their page is not rendered
for k in list(ss.keys()):
    if any(k.startswith(f"{f}_") for f in INPUT_FIELDS) or k in ("n_people", "t_weight", "open_now", "vibe_friend"):
        ss[k] = ss[k]

ss.setdefault("page", "where")
ss.setdefault("n_people", 3)
ss.setdefault("t_weight", 70)
ss.setdefault("open_now", False)
for i in range(MAX_PEOPLE):
    ss.setdefault(f"name_{i}", f"Friend {i + 1}")
    ss.setdefault(f"line_{i}", "Green")
    ss.setdefault(f"station_{i}", stations_on(ss[f"line_{i}"])[0])
    ss.setdefault(f"budget_{i}", 20)
    ss.setdefault(f"mood_{i}", "Chill")
    for f in ("activities", "cuisines", "dietary"):
        ss.setdefault(f"{f}_{i}", [])
    ss.setdefault(f"indoor_outdoor_{i}", "Either")
    ss.setdefault(f"noise_{i}", "Either")

DEMO = [
    dict(name="Stephanie", station="Boston University Central", budget=20, mood="Starving",
         activities=["Food"], cuisines=["Asian"], dietary=[], indoor_outdoor="Indoor", noise="Either"),
    dict(name="Alex", station="Harvard", budget=15, mood="Chill",
         activities=["Food", "Cafe"], cuisines=["Asian", "Mexican"], dietary=["Vegetarian"],
         indoor_outdoor="Either", noise="Either"),
    dict(name="Jordan", station="Northeastern University", budget=25, mood="Dateish",
         activities=["Museum", "Dessert"], cuisines=["Italian"], dietary=[],
         indoor_outdoor="Outdoor", noise="Quiet"),
]


def load_demo():
    ss["n_people"] = len(DEMO)
    for i, p in enumerate(DEMO):
        p = dict(p)
        if p["station"] not in STATION_NAMES:          # tolerate different station naming
            key = p["station"].split()[0].lower()
            p["station"] = next((s for s in STATION_NAMES if key in s.lower()), STATION_NAMES[0])
        p["line"] = line_of(p["station"])
        for k, v in p.items():
            ss[f"{k}_{i}"] = v


def people():
    out = []
    for i in range(int(ss["n_people"])):
        out.append(dict(
            name=(ss[f"name_{i}"] or f"Friend {i + 1}").strip() or f"Friend {i + 1}",
            line=ss[f"line_{i}"], station=ss[f"station_{i}"], budget=int(ss[f"budget_{i}"]),
            mood=ss[f"mood_{i}"] or "Chill",
            activities=list(ss[f"activities_{i}"] or []), cuisines=list(ss[f"cuisines_{i}"] or []),
            dietary=list(ss[f"dietary_{i}"] or []),
            indoor_outdoor=ss[f"indoor_outdoor_{i}"] or "Either", noise=ss[f"noise_{i}"] or "Either"))
    # names must be unique: they are used as table columns
    seen = {}
    for p in out:
        if p["name"] in seen:
            seen[p["name"]] += 1
            p["name"] = f"{p['name']} ({seen[p['name']]})"
        else:
            seen[p["name"]] = 1
    return out


def signature():
    return json.dumps([people(), ss["t_weight"], ss["open_now"]], sort_keys=True)


def go(page):
    ss["page"] = page


def compute():
    ppl = people()
    top, scores, msg = L.recommend(ppl, places, stations, open_now=ss["open_now"],
                                   transit_weight=ss["t_weight"] / 100)
    res = dict(sig=signature(), people=ppl, msg=msg, top=top, scores=scores)
    if not msg:
        winner, _, _ = L.hardest_to_please(ppl, scores, None)
        res["winner"] = winner
        if winner:
            pool = load_roasts()
            last = ss.get("last_roast")
            choices = [r for r in pool if r != last] or pool
            roast = random.choice(choices)
            ss["last_roast"] = roast
            person = next(p for p in ppl if p["name"] == winner)
            res.update(roast=roast.format(name=winner), person=person,
                       reasons=L.why_hardest(person, top, places),
                       compromise=L.best_compromise(person, top))
    ss["res"] = res
    ss["page"] = "results1"


# ---------------------------------------------------------------- shared bits
LINE_DOT = {"Red": "🔴", "Orange": "🟠", "Blue": "🔵", "Green": "🟢"}
MOOD_ICON = {"Starving": "🍔", "Chill": "☕", "Dateish": "💕", "Adventurous": "🧗", "Productive": "💻"}
ACT_ICON = {"Food": "🍜", "Cafe": "☕", "Dessert": "🍰", "Outdoor": "🌳", "Museum": "🏛️",
            "Shopping": "🛍️", "Nightlife": "🎤"}
IO_ICON = {"Indoor": "🏠", "Outdoor": "🌲", "Either": "🤷"}
NOISE_ICON = {"Quiet": "🔇", "Lively": "🎵", "Either": "📶"}


def stepper(active):
    names = ["Where", "Vibe", "Meet"]
    parts = []
    for n, name in enumerate(names, 1):
        cls = "done" if n < active else ("on" if n == active else "")
        mark = "✓" if n < active else str(n)
        parts.append(f'<div class="s"><div class="dot {cls}">{mark}</div>{name}</div>')
        if n < 3:
            parts.append('<div class="ln"></div>')
    st.markdown(f'<div class="mmh-stepper">{"".join(parts)}</div>', unsafe_allow_html=True)


def head_card(title, sub, icon=""):
    st.markdown(f'<div class="mmh-head"><div class="t">{icon} <span>{title}</span></div>'
                f'<div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def avatar(i, small=False):
    """Neutral friend icon: circle in the friend's T-line color with their initial."""
    name = (ss.get(f"name_{i}") or f"Friend {i + 1}").strip() or "?"
    color = LINE_HEX.get(ss.get(f"line_{i}"), "#111")
    return f'<span class="mmh-av{" sm" if small else ""}" style="background:{color}">{esc(name[0].upper())}</span>'


def avatar_txt(i):
    """Plain-text version for widgets that can't render HTML."""
    return LINE_DOT.get(ss.get(f"line_{i}"), "⚪")


st.markdown('<div class="mmh-brand">BOSTONHACKS 2026</div>', unsafe_allow_html=True)
if "sample" in pl_path:
    st.caption("ℹ️ Using SAMPLE places. Upload the real file as data/places.csv to switch.")

# ================================================================ PAGE 1: WHERE
if ss["page"] == "where":
    st.markdown('<div class="mmh-hero">MEET ME HALFWAY 🚇</div>', unsafe_allow_html=True)
    st.markdown('<div class="mmh-tag">Different stops. One fair destination.</div>', unsafe_allow_html=True)
    st.markdown('<div class="mmh-route-art" aria-hidden="true"><div class="track green"></div><div class="track red"></div><div class="stop"></div></div>', unsafe_allow_html=True)
    stepper(1)
    head_card("Where's everyone starting?", "Add your crew and each person's MBTA starting point.", "🚇")

    c1, c2, _ = st.columns([1.2, 1, 2])
    c1.button("🎲 Load demo group", on_click=load_demo, use_container_width=True)
    c2.number_input("friends", 2, MAX_PEOPLE, key="n_people", label_visibility="collapsed")

    for i in range(int(ss["n_people"])):
        row, edit = st.columns([6, 1], vertical_alignment="center")
        with row:
            st.markdown(f"""
<div class="mmh-friend"><div class="av">{avatar(i)}</div>
  <div><div class="nm">{esc(ss[f'name_{i}'] or f'Friend {i + 1}')}</div>
  <span class="mmh-pill" style="background:{LINE_HEX.get(ss[f'line_{i}'], '#111')}">{esc(ss[f'line_{i}'])} Line</span> &nbsp;📍 {esc(ss[f'station_{i}'])}</div></div>""",
                        unsafe_allow_html=True)
        with edit:
            with st.popover("✏️", use_container_width=True):
                st.text_input("Name", key=f"name_{i}")
                st.selectbox("T line", LINES, key=f"line_{i}")
                opts = stations_on(ss[f"line_{i}"])
                if ss.get(f"station_{i}") not in opts:
                    ss[f"station_{i}"] = opts[0]
                st.selectbox("Starting stop", opts, key=f"station_{i}")
    st.write("")
    st.button("Next: Pick Your Vibe →", type="primary", on_click=go, args=("vibe",), use_container_width=True)

# ================================================================ PAGE 2: VIBE
elif ss["page"] == "vibe":
    stepper(2)
    head_card("What are we in the mood for?", "Set each friend's preferences.", "✨")
    ppl = people()
    n = len(ppl)
    if ss.get("vibe_friend") is None or ss["vibe_friend"] >= n:
        ss["vibe_friend"] = 0
    st.segmented_control("Friend", list(range(n)), key="vibe_friend", label_visibility="collapsed",
                         format_func=lambda k: f"{avatar_txt(k)} {ppl[k]['name']}")
    i = ss["vibe_friend"] if ss["vibe_friend"] is not None else 0

    with st.container(border=True):
        st.markdown(f"#### {esc(ppl[i]['name'])}'s preferences")
        a, b = st.columns(2)
        with a:
            st.slider("💵 Budget (per person, $)", 0, 60, key=f"budget_{i}")
            st.pills("Want to do", L.ACTIVITIES, selection_mode="multi", key=f"activities_{i}",
                     format_func=lambda x: f"{ACT_ICON.get(x, '')} {x}")
            st.pills("Cuisines", L.CUISINES, selection_mode="multi", key=f"cuisines_{i}")
            st.pills("Dietary", L.DIETARY, selection_mode="multi", key=f"dietary_{i}")
        with b:
            st.pills("Mood", L.MOODS, selection_mode="single", key=f"mood_{i}",
                     format_func=lambda x: f"{MOOD_ICON.get(x, '')} {x}")
            st.segmented_control("Indoor / Outdoor", L.IO_CHOICES, key=f"indoor_outdoor_{i}",
                                 format_func=lambda x: f"{IO_ICON.get(x, '')} {x}")
            st.segmented_control("Noise", L.NOISE_CHOICES, key=f"noise_{i}",
                                 format_func=lambda x: f"{NOISE_ICON.get(x, '')} {'Any' if x == 'Either' else x}")
            st.caption("Leave Want to do / Cuisines empty = anything works.")

    with st.expander("⚙️ Ranking settings"):
        x, y = st.columns([2, 1])
        x.slider("🚇 How much should T convenience matter? (%)", 0, 100, step=10, key="t_weight",
                 help="70 = default. 0 = only preferences, 100 = only short, fair T trips.")
        y.toggle("Open now only", key="open_now")

    b1, b2 = st.columns([1, 2])
    b1.button("← Back", on_click=go, args=("where",), use_container_width=True)
    b2.button("Next: Meet Halfway →", type="primary", on_click=compute, use_container_width=True)

# ================================================================ RESULTS
else:
    res = ss.get("res")
    if res is None:
        st.info("No results yet.")
        st.button("Start →", on_click=go, args=("where",))
        st.stop()
    if res["sig"] != signature():
        st.warning("You changed some inputs — these results are out of date.")
        st.button("🔄 Recalculate", type="primary", on_click=compute)
        st.stop()
    if res["msg"]:
        stepper(3)
        st.warning(res["msg"])
        st.button("← Edit the vibe", on_click=go, args=("vibe",))
        st.stop()

    top, scores, ppl = res["top"], res["scores"], res["people"]
    idx_of = {p["name"]: k for k, p in enumerate(ppl)}
    w = ss["t_weight"]
    best = top.iloc[0]
    f = L.fairness(best)

    # ------------------------------------------------ RESULTS PAGE 1: MEET
    if ss["page"] == "results1":
        stepper(3)
        head_card("Let's meet halfway!", "A fair meeting point based on MBTA convenience and your group's preferences.", "📍")

        st.markdown(f"""
<div class="mmh-toppick"><div class="tag">⭐ TOP PICK</div>
  <div class="mmh-bubble">Group Match<b>{best['avg_match']:.0%}</b></div>
  <div style="flex:1">
    <div class="mmh-big">{esc(best['name'])}</div>
    <div style="margin:6px 0">{TYPE_ICON.get(str(best['type']), '')} {esc(best['type'])} &nbsp;·&nbsp;
      <span class="mmh-chip">~${best['avg_cost']:.0f} per person</span> &nbsp;·&nbsp; {esc(best['indoor_outdoor'])} · {esc(best['noise'])}
      &nbsp;·&nbsp; 🕒 {esc(best['open'])}–{esc(best['close'])}</div>
    <div>Ⓣ <b>{esc(best['nearest_station'])}</b> {lines_pills(best['nearest_lines'])}</div>
    <div style="margin-top:8px"><b>🚇 T Convenience {best['transit']:.0%}</b>{bar(best['transit'], '#3575DE')}</div>
    <div style="font-size:.85rem">Overall {best['total']:.0%} = {w}% T convenience + {100 - w}% group match · full rules on the next page</div>
  </div>
</div>""", unsafe_allow_html=True)

        left, right = st.columns([3, 2])
        with left:
            rows = ""
            for p in ppl:
                mins, direct, walk = best["trips"][p["name"]]
                badge = '<span class="mmh-badge ok">Direct</span>' if direct else '<span class="mmh-badge tr">Transfer</span>'
                rows += (f'<div class="mmh-row"><div>{avatar(idx_of[p["name"]], True)} <b>{esc(p["name"])}</b><br>'
                         f'<span style="font-size:.85rem">{esc(p["station"])} {line_pill(p["line"])}</span></div>'
                         f'<div style="text-align:right">🚇 <b>~{mins} min</b> {badge}<br>'
                         f'<span style="font-size:.85rem">+ {walk} min walk</span></div></div>')
            st.markdown(f'<div class="mmh-card"><span class="mmh-hl">🚇 How everyone gets there</span>'
                        f'{rows}<div style="font-size:.8rem;margin-top:6px">Estimated times — not live MBTA data.</div></div>',
                        unsafe_allow_html=True)
        with right:
            st.markdown(f"""
<div class="mmh-card"><span class="mmh-hl">⚖️ Fairness insight</span>
  <div class="mmh-row"><span>🔴 Longest trip</span><b>{esc(f['longest'])} (~{f['longest_min']} min)</b></div>
  <div class="mmh-row"><span>🟢 Shortest trip</span><b>{esc(f['shortest'])} (~{f['shortest_min']} min)</b></div>
  <div class="mmh-row"><span>🔵 Difference</span><b>{f['gap']} min</b></div>
  <p style="margin:8px 0 0 0">{esc(f['verdict'])}</p>
</div>""", unsafe_allow_html=True)

        mcol, ocol = st.columns([3, 2])
        with mcol:
            st.markdown('<span class="mmh-hl">🗺️ Map: stops & recommended places</span>',
                        unsafe_allow_html=True)
            st_idx = stations.drop_duplicates("station_name").set_index("station_name")
            pts = [dict(label=f"{p['station']} ({p['name']})", lat=float(st_idx.loc[p["station"]].lat),
                        lon=float(st_idx.loc[p["station"]].lon), color=LINE_RGB.get(p["line"], [17, 17, 17]), r=110)
                   for p in ppl]
            pts += [dict(label=f"#{int(r['rank'])} {r['name']}", lat=float(r["lat"]), lon=float(r["lon"]),
                         color=[210, 31, 54] if r["rank"] == 1 else [247, 224, 0], r=170 if r["rank"] == 1 else 110)
                    for _, r in top.iterrows()]
            mdf = pd.DataFrame(pts)
            mdf["short"] = mdf["label"].str.split(" ").str[0]   # "#1", "#2"… keeps labels from piling up
            st.pydeck_chart(pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(latitude=mdf.lat.mean(), longitude=mdf.lon.mean(), zoom=12),
                layers=[
                    pdk.Layer("ScatterplotLayer", mdf, get_position="[lon, lat]", get_fill_color="color",
                              get_radius="r", stroked=True, get_line_color=[17, 17, 17], line_width_min_pixels=2,
                              pickable=True),
                    pdk.Layer("TextLayer", mdf[mdf["label"].str.startswith("#")], get_position="[lon, lat]",
                              get_text="short", get_size=14, get_color=[17, 17, 17], get_pixel_offset=[0, -20]),
                ],
                views=[pdk.View(type="MapView", controller={"scrollZoom": False, "dragPan": True,
                                                            "doubleClickZoom": True, "touchZoom": True})],
                tooltip={"text": "{label}"},
            ), height=300)
            st.caption("Colored dots = friends' starting stops (by line) · 🔴 #1 place · 🟡 alternatives · tap a dot for its name. Pins only, not real routes.")
        with ocol:
            st.markdown('<span class="mmh-hl">🌟 Other great options</span>',
                        unsafe_allow_html=True)
            for _, r in top.iloc[1:].iterrows():
                with st.expander(f"{TYPE_ICON.get(str(r['type']), '📍')} {r['name']} · match {r['avg_match']:.0%}"):
                    st.markdown(f"{esc(r['type'])} · ~${r['avg_cost']:.0f}/person · Ⓣ {esc(r['nearest_station'])} "
                                f"{lines_pills(r['nearest_lines'])}<br>🚇 T convenience **{r['transit']:.0%}** · "
                                f"❤️ Group match **{r['avg_match']:.0%}**", unsafe_allow_html=True)
                    for p in ppl:
                        mins, direct, walk = r["trips"][p["name"]]
                        st.caption(f"{p['name']}: ~{mins} min · {'direct' if direct else '1 transfer'} · {walk} min walk")
            if len(top) == 1:
                st.caption("Only one place fits everyone right now.")

        st.markdown('<div class="mmh-split-title"><span class="mmh-hl">✨ Next stop: the group drama</span>'
                    '<span class="mmh-sticker">WHO IS THE PICKIEST? 👀</span></div>', unsafe_allow_html=True)
        if res.get("winner"):
            faces = "".join(avatar(k) for k in range(len(ppl)))
            st.markdown(f'''<div class="mmh-mystery"><div style="font-size:2.2rem">🥁 👑 🥁</div>
<div class="q">???</div><p><b>One of you made this way harder than it needed to be.</b></p>
<p>Ready to find out who?</p><div class="ppl">{faces}</div></div>''', unsafe_allow_html=True)
            reveal = "🎁 Reveal the Hardest to Please →"
        else:
            reveal = "🤝 See everyone's match →"
        n1, n2 = st.columns([1, 2])
        n1.button("← Edit the vibe", on_click=go, args=("vibe",), use_container_width=True)
        n2.button(reveal, type="primary", on_click=go, args=("results2",), use_container_width=True)

    # ------------------------------------------------ RESULTS PAGE 2: HARDEST TO PLEASE
    else:
        stepper(3)
        head_card("Hardest to Please", "Who stretched the group the most — and how to compromise.", "😈")
        winner = res.get("winner")
        if not winner:
            st.markdown('<div class="mmh-card mmh-hot"><div class="mmh-big">🤝 Everyone is equally easy to please.</div>'
                        '<p>Suspiciously wholesome. No roast today.</p></div>', unsafe_allow_html=True)
        else:
            avg = scores.mean(axis=0)
            roast = res["roast"]
            st.markdown(f"""
<div class="mmh-banner">
  <div style="flex:1">
    <div class="mmh-sticker">🚨 MAIN CHARACTER ALERT 🚨</div>
    <div class="c" style="margin-top:13px">The award goes to <span>{esc(winner)}!</span></div>
    <div class="roast">💅 {esc(roast)}</div>
    <div style="margin-top:13px;font-weight:600">On our top picks: {avg[winner]:.0%} average match
      &nbsp;·&nbsp; Group average: {avg.mean():.0%}</div>
  </div>
  <div style="font-size:4.5rem;line-height:1;text-align:center">👑</div>
</div>""", unsafe_allow_html=True)

            c = res["compromise"]
            if c:
                tip = (f"💡 <b>Meet halfway:</b> {esc(winner)}, change <b>{esc(c['label'])}</b> from <i>{esc(c['old'])}</i> "
                       f"to <i>{esc(c['new'])}</i> and your match jumps "
                       f"<span class='mmh-hl'>{c['before']:.0%} → {c['after']:.0%}</span>")
            else:
                tip = (f"💡 We couldn't find a single soft-preference change that improves {esc(winner)}'s "
                       "match on these top picks. Try exploring different locations or group priorities.")
            st.markdown(f'<div class="mmh-card mmh-blue" style="font-size:1.15rem">{tip}'
                        f'<div style="font-size:.8rem;margin-top:6px">What-if comparison on the same top picks (not a new ranking). '
                        f'We never suggest dropping a budget or dietary need.</div></div>', unsafe_allow_html=True)

        st.markdown(f'<div class="mmh-strip">🚇 Longest ride to the #1 pick: <b>{esc(f["longest"])}</b> '
                    f'(~{f["longest_min"]} min). Trips differ by only <b>{f["gap"]} min</b> — that\'s meeting halfway.</div>',
                    unsafe_allow_html=True)

        if winner:
            person = res["person"]
            misses = {bd["field"] for _, r in top.iterrows() for bd in L.match_breakdown(person, r) if not bd["matched"]}
            chips = [
                ("mood", f"{MOOD_ICON.get(person['mood'], '')} Feeling {person['mood']}"),
                ("activities", f"🎯 Wants {', '.join(person['activities']) or 'anything'}"),
                ("cuisines", f"🍴 Likes {', '.join(person['cuisines']) or 'any cuisine'}"),
                ("indoor_outdoor", f"{IO_ICON.get(person['indoor_outdoor'], '')} Prefers {person['indoor_outdoor']}"),
                ("noise", f"{NOISE_ICON.get(person['noise'], '')} {person['noise']} vibe"),
            ]
            chip_html = "".join(f'<span class="mmh-pchip {"miss" if k in misses else "hit"}">{esc(t)}</span>'
                                for k, t in chips)
            chip_html += f'<span class="mmh-pchip">💵 Budget ≤ ${person["budget"]}</span>'
            for d in person["dietary"]:
                chip_html += f'<span class="mmh-pchip">🥗 {esc(d)}</span>'
            items = "".join(f"<li>{md(r)}</li>" for r in res["reasons"]) or "<li>No mismatches found.</li>"
            st.markdown(f'<div class="mmh-card"><span class="mmh-hl" style="font-size:1.2rem">'
                        f'🔍 Why {esc(winner)}?</span><div style="margin:10px 0">{chip_html}</div>'
                        f'<div style="font-size:.8rem">🟥 clashed with at least one top pick · 🟩 matched every top pick</div>'
                        f'<ul style="margin-top:8px">{items}</ul></div>', unsafe_allow_html=True)
        st.markdown('<div class="mmh-split-title"><span class="mmh-hl">🎯 Who actually liked each place?</span>'
                    '<span class="mmh-sticker">RECEIPTS INCLUDED 🧾</span></div>', unsafe_allow_html=True)
        st.caption("These percentages are computed from five preference checks per friend, not made-up demo values.")
        mt = L.match_table(scores)

        def cell(v):
            bg = "#CDEFD8" if v >= 70 else ("#FFF3A6" if v >= 40 else "#F9CED6")
            return f'<td style="background:{bg}"><b>{v}%</b></td>'

        icons = dict(zip(top["display_label"], top["type"]))
        head_row = "".join(f"<th>{avatar(idx_of.get(c, 0), True)} {esc(c)}</th>" for c in mt.columns)
        body = "".join(f"<tr><td>{TYPE_ICON.get(str(icons.get(idx)), '📍')} {esc(idx)}</td>"
                       f"{''.join(cell(int(v)) for v in row)}</tr>" for idx, row in mt.iterrows())
        st.markdown(f'<table class="mmh-t"><tr><th>📊 Place</th>{head_row}</tr>{body}</table>', unsafe_allow_html=True)
        st.caption("🟩 70%+ · 🟨 40–69% · 🟥 under 40% — share of the 5 preferences each place satisfies")

        with st.expander("🔎 Inspect a place: what matched for each friend?"):
            pick = st.selectbox("Place", top["display_label"].tolist(), key="inspect_place")
            prow = top[top["display_label"] == pick].iloc[0]
            cols = st.columns(len(ppl))
            for col, p in zip(cols, ppl):
                with col:
                    bd = L.match_breakdown(p, prow)
                    score = sum(x["matched"] for x in bd)
                    lines = "".join(
                        f'<div class="mmh-row" style="font-size:.85rem"><span>{"✅" if x["matched"] else "❌"} {esc(x["label"])}</span>'
                        f'<span>wants <i>{esc(x["wanted"])}</i> · has <i>{esc(x["place_value"])}</i></span></div>' for x in bd)
                    st.markdown(f'<div class="mmh-card"><b>{avatar(idx_of[p["name"]], True)} {esc(p["name"])}</b> — '
                                f'{score}/5 ({score * 20}%){lines}</div>', unsafe_allow_html=True)

        st.markdown(f"""
<div class="mmh-card"><span class="mmh-hl" style="font-size:1.2rem">📊 How the score works (same rules for every group)</span>
  <div class="mmh-formula">Score = {100 - w}% Group match + {w}% T convenience</div>
  <ul style="font-size:.92rem">
<li><b>Hard filters first:</b> over the lowest budget, or missing a vegetarian/halal option someone needs → removed.</li>
<li><b>Trip minutes</b> = {L.WAIT_MIN} min wait + ride between stations + walk from station (+{L.TRANSFER_MIN} min if you transfer). Estimates only.</li>
<li><b>T convenience</b> = 70% the farthest friend's trip is short + 30% everyone's trip is a similar length.</li>
<li><b>Group match</b> = mood, activity, cuisine, indoor/outdoor, noise — each worth 20% per friend.</li>
<li><b>Hardest to Please</b> = lowest average match on the top picks.</li>
  </ul>
</div>""", unsafe_allow_html=True)

        n1, n2 = st.columns(2)
        n1.button("← Back to meeting point", on_click=go, args=("results1",), use_container_width=True)
        n2.button("✏️ Edit the vibe", on_click=go, args=("vibe",), use_container_width=True)
