import streamlit as st
import pandas as pd
import json
import pdfplumber
import os
from datetime import datetime, date
import re
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DATA_FILE = "coi_data.csv"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
NOTES_FILE = "vendor_notes.json"

st.set_page_config(
    layout="wide",
    page_title="Aberdeen Mall — COI Tracker",
    page_icon="🏢"
)

# ─────────────────────────────────────────────
# CUSTOM CSS — dark industrial aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Barlow+Condensed:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Barlow Condensed', sans-serif;
    background-color: #0f1117;
    color: #e0e0e0;
}

.main { background-color: #0f1117; }

h1, h2, h3 {
    font-family: 'Barlow Condensed', sans-serif;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.stButton > button {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    background-color: #1e2130;
    color: #e0e0e0;
    border: 1px solid #3a3f55;
    border-radius: 2px;
    padding: 4px 12px;
    transition: all 0.2s;
}
.stButton > button:hover {
    background-color: #e05c2a;
    border-color: #e05c2a;
    color: white;
}

.metric-card {
    background: linear-gradient(135deg, #1a1e2e 0%, #141824 100%);
    border: 1px solid #2a2f45;
    border-radius: 4px;
    padding: 18px 22px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}
.metric-card.valid::before { background: #2ecc71; }
.metric-card.warning::before { background: #f39c12; }
.metric-card.critical::before { background: #e74c3c; }
.metric-card.total::before { background: #3498db; }

.metric-number {
    font-family: 'Space Mono', monospace;
    font-size: 2.4em;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 4px;
}
.metric-label {
    font-size: 0.85em;
    letter-spacing: 0.15em;
    color: #888;
    text-transform: uppercase;
}

.status-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 2px;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-valid { background: #1a3d2b; color: #2ecc71; border: 1px solid #2ecc71; }
.badge-warning { background: #3d2e0a; color: #f39c12; border: 1px solid #f39c12; }
.badge-critical { background: #3d0f0f; color: #e74c3c; border: 1px solid #e74c3c; }
.badge-expired { background: #2a0808; color: #c0392b; border: 1px solid #c0392b; }
.badge-inactive { background: #222; color: #666; border: 1px solid #444; }

.vendor-row {
    background: #141824;
    border: 1px solid #2a2f45;
    border-radius: 3px;
    padding: 10px 14px;
    margin-bottom: 6px;
}

.section-header {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.1em;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #888;
    border-bottom: 1px solid #2a2f45;
    padding-bottom: 6px;
    margin: 18px 0 12px 0;
}

.alert-banner {
    background: #2a0f0f;
    border-left: 4px solid #e74c3c;
    padding: 10px 16px;
    margin-bottom: 8px;
    border-radius: 0 3px 3px 0;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
}

.stTabs [data-baseweb="tab-list"] {
    background-color: #141824;
    border-bottom: 1px solid #2a2f45;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1em;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #888;
    padding: 10px 20px;
}
.stTabs [aria-selected="true"] {
    color: #e05c2a !important;
    border-bottom: 2px solid #e05c2a !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #2a2f45;
}

/* ── Input fields & text areas: white bg, dark text ── */
.stTextInput > div > div > input,
.stTextInput > div > div {
    background-color: #ffffff !important;
    color: #1a1a2e !important;
    border-color: #3a3f55 !important;
}
.stSelectbox > div > div,
.stSelectbox > div > div > div {
    background-color: #ffffff !important;
    color: #1a1a2e !important;
    border-color: #3a3f55 !important;
}
/* Dropdown menu options */
[data-baseweb="select"] > div,
[data-baseweb="popover"] li {
    background-color: #ffffff !important;
    color: #1a1a2e !important;
}
/* Text area (PDF preview) */
.stTextArea > div > div > textarea {
    background-color: #f8f8f8 !important;
    color: #1a1a2e !important;
    border-color: #3a3f55 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 12px !important;
}
/* Date input */
.stDateInput > div > div > input {
    background-color: #ffffff !important;
    color: #1a1a2e !important;
    border-color: #3a3f55 !important;
}
/* Search bar */
.stTextInput input::placeholder {
    color: #999 !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SEED DATA — Aberdeen Mall Contractors
# ─────────────────────────────────────────────
SEED_DATA = [
    {"Vendor": "Aces Asphalt Repair",             "COI Expiry": "2026-06-02",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "N/A",        "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Advanced Electrical Systems",      "COI Expiry": "2027-04-01",  "WorkSafe Expiry": "2026-07-01", "OHS Plan": "Yes",        "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Arcona Roofing",                   "COI Expiry": "2026-12-01",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "N/A",        "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Artistic Sign Services Ltd.",      "COI Expiry": "2022-09-12",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "N/A",        "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Entrance Systems Assa Abloy",      "COI Expiry": "",            "WorkSafe Expiry": "2024-04-01", "OHS Plan": "N/A",        "Active": True,  "Email": "", "Notes": "No COI on file", "WCB Number": ""},
    {"Vendor": "A&T Project Developments",         "COI Expiry": "2026-06-01",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "Yes",        "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "BA Dawson Blacktop Ltd.",          "COI Expiry": "2026-04-30",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "BEST Service Pros",                "COI Expiry": "2025-09-30",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Central Interior Rebuilders",      "COI Expiry": "2025-11-06",  "WorkSafe Expiry": "2025-01-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Chubb/Edwards",                    "COI Expiry": "2025-12-31",  "WorkSafe Expiry": "2025-08-29", "OHS Plan": "Yes",        "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Cona Flooring",                    "COI Expiry": "2026-01-15",  "WorkSafe Expiry": "2026-11-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Culture Care Landscaping",         "COI Expiry": "2027-04-11",  "WorkSafe Expiry": "2026-04-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Custom Air Conditioning",          "COI Expiry": "2025-07-31",  "WorkSafe Expiry": "2025-01-01", "OHS Plan": "Electronic", "Active": False, "Email": "", "Notes": "No longer contractor. See Reliatech.", "WCB Number": ""},
    {"Vendor": "Dawson Civil",                     "COI Expiry": "2025-11-01",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "Electronic", "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Evans Fire",                       "COI Expiry": "2025-03-15",  "WorkSafe Expiry": "2024-10-01", "OHS Plan": "",           "Active": False, "Email": "", "Notes": "Not currently using", "WCB Number": ""},
    {"Vendor": "Farmer Stratta",                   "COI Expiry": "2023-07-22",  "WorkSafe Expiry": "2023-01-01", "OHS Plan": "",           "Active": False, "Email": "", "Notes": "Not currently using", "WCB Number": ""},
    {"Vendor": "Guardteck Security",               "COI Expiry": "2023-03-01",  "WorkSafe Expiry": "2023-04-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "GFL",                              "COI Expiry": "2026-06-01",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Hardaker Concrete",                "COI Expiry": "2023-06-24",  "WorkSafe Expiry": "2023-01-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Howell Electric",                  "COI Expiry": "2023-01-23",  "WorkSafe Expiry": "2022-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Interior Locksmith",               "COI Expiry": "2025-11-10",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Interior Fire",                    "COI Expiry": "2025-08-02",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Interior Plumbing & Heating",      "COI Expiry": "2020-01-25",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": False, "Email": "", "Notes": "Not currently using", "WCB Number": ""},
    {"Vendor": "Job Squad (The)",                  "COI Expiry": "2026-06-02",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Justlane Sweeping",                "COI Expiry": "2025-08-01",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "1415040 BC Ltd", "WCB Number": ""},
    {"Vendor": "KJA Consulting Inc.",              "COI Expiry": "2027-12-01",  "WorkSafe Expiry": "2027-01-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "KTA Mechanical Inc.",              "COI Expiry": "2026-01-24",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Keltech Environmental",            "COI Expiry": "2026-12-01",  "WorkSafe Expiry": "2026-01-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Kimco Controls",                   "COI Expiry": "2026-01-29",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "Electronic", "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Klean Tech",                       "COI Expiry": "2025-08-28",  "WorkSafe Expiry": "2026-04-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Kone",                             "COI Expiry": "2026-01-01",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Lyons Landscaping",                "COI Expiry": "2025-05-05",  "WorkSafe Expiry": "2024-07-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "MGBA Architecture",               "COI Expiry": "2026-08-30",  "WorkSafe Expiry": "2026-01-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "MTC Plumbing & Drain Cleaning",    "COI Expiry": "2026-08-01",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "Roto Rooter", "WCB Number": ""},
    {"Vendor": "Nutech Safety",                    "COI Expiry": "2025-04-30",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Olleck Contracting Ltd",           "COI Expiry": "2026-07-09",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Pinchin",                          "COI Expiry": "2025-10-30",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "R & D Construction",               "COI Expiry": "2026-09-27",  "WorkSafe Expiry": "2026-07-01", "OHS Plan": "Yes",        "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Response Fire Systems Ltd",        "COI Expiry": "2024-01-20",  "WorkSafe Expiry": "2023-07-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Riteway Fence",                    "COI Expiry": "2020-10-31",  "WorkSafe Expiry": "2020-04-01", "OHS Plan": "",           "Active": False, "Email": "", "Notes": "Not currently using", "WCB Number": ""},
    {"Vendor": "Service Plus",                     "COI Expiry": "2024-04-24",  "WorkSafe Expiry": "2026-04-01", "OHS Plan": "Yes",        "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "See Thru Window Cleaners (Ever Clear)", "COI Expiry": "2025-04-16", "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",    "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Service Master",                   "COI Expiry": "2019-02-14",  "WorkSafe Expiry": "2020-07-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Southwest Glass LTD",              "COI Expiry": "2025-08-21",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Spa Hills",                        "COI Expiry": "2026-09-22",  "WorkSafe Expiry": "2026-04-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Sun Valley Painting",              "COI Expiry": "2025-04-10",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Sunny Green Environmental",        "COI Expiry": "2026-07-01",  "WorkSafe Expiry": "2026-04-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Syndicate Lines and Contracting",  "COI Expiry": "2024-09-26",  "WorkSafe Expiry": "2024-01-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Total Power",                      "COI Expiry": "2025-11-30",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Total Vent Cleaning",              "COI Expiry": "2026-02-28",  "WorkSafe Expiry": "2026-04-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "N & J Holdings", "WCB Number": ""},
    {"Vendor": "Troy Life & Fire Safety",          "COI Expiry": "2025-10-01",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Twin River Plumbing & Heating",    "COI Expiry": "2025-09-15",  "WorkSafe Expiry": "2026-01-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Vics Fire & Safety",               "COI Expiry": "2023-06-19",  "WorkSafe Expiry": "2024-01-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Westcoast Road Marking",           "COI Expiry": "2026-03-27",  "WorkSafe Expiry": "2025-10-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Western Roofing",                  "COI Expiry": "2025-07-31",  "WorkSafe Expiry": "2025-07-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "WHM Wicke Herfst Maver",           "COI Expiry": "2024-08-02",  "WorkSafe Expiry": "2024-07-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Underwraps",                       "COI Expiry": "2020-08-08",  "WorkSafe Expiry": "2023-01-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
    {"Vendor": "Underhill Geomatics",              "COI Expiry": "2024-09-12",  "WorkSafe Expiry": "2024-04-01", "OHS Plan": "",           "Active": True,  "Email": "", "Notes": "", "WCB Number": ""},
]

# ─────────────────────────────────────────────
# DATA FUNCTIONS
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# NOTES / COMMENTS FEED
# ─────────────────────────────────────────────
def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE) as f:
            return json.load(f)
    return {}

def save_notes(notes):
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)

def add_note(vendor, text, author="Facilities"):
    notes = load_notes()
    if vendor not in notes:
        notes[vendor] = []
    notes[vendor].insert(0, {
        "text": text,
        "author": author,
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_notes(notes)

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Ensure all columns exist
        for col in ["Vendor", "COI Expiry", "WorkSafe Expiry", "OHS Plan", "Active", "Email", "Notes", "File", "WCB Number"]:
            if col not in df.columns:
                df[col] = ""
        return df
    # First run — seed with Aberdeen Mall data
    df = pd.DataFrame(SEED_DATA)
    df["File"] = ""
    save_data(df)
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def compute_status(expiry_str, active=True):
    if not active:
        return "Inactive", 9999
    if not expiry_str or pd.isna(expiry_str) or str(expiry_str).strip() == "":
        return "No COI", -9999
    try:
        exp = pd.to_datetime(expiry_str).date()
        days = (exp - date.today()).days
        if days < 0:
            return "Expired", days
        elif days <= 30:
            return "Critical", days
        elif days <= 90:
            return "Warning", days
        else:
            return "Valid", days
    except:
        return "Unknown", 0

def build_view(df):
    df = df.copy()
    df["Active"] = df["Active"].astype(str).str.lower().isin(["true", "1", "yes"])

    coi_statuses, coi_days, ws_statuses, ws_days = [], [], [], []
    for _, row in df.iterrows():
        cs, cd = compute_status(row.get("COI Expiry", ""), row["Active"])
        ws, wd = compute_status(row.get("WorkSafe Expiry", ""), row["Active"])
        coi_statuses.append(cs)
        coi_days.append(cd)
        ws_statuses.append(ws)
        ws_days.append(wd)

    df["COI Status"] = coi_statuses
    df["COI Days Left"] = coi_days
    df["WS Status"] = ws_statuses
    df["WS Days Left"] = ws_days
    return df

df = load_data()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="padding: 10px 0 20px 0; border-bottom: 1px solid #2a2f45; margin-bottom: 24px;">
    <div style="font-family: 'Barlow Condensed', sans-serif; font-size: 0.8em; letter-spacing: 0.25em; color: #e05c2a; text-transform: uppercase; margin-bottom: 2px;">Aberdeen Mall</div>
    <div style="font-family: 'Barlow Condensed', sans-serif; font-size: 2.2em; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; line-height: 1;">Contractor Compliance Tracker</div>
    <div style="font-family: 'Space Mono', monospace; font-size: 0.75em; color: #666; margin-top: 4px;">COI · WORKSAFEBC · OHS PLAN MANAGEMENT</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# METRICS ROW
# ─────────────────────────────────────────────
view = build_view(df)
active_view = view[view["Active"] == True]

total = len(active_view)
valid = len(active_view[active_view["COI Status"] == "Valid"])
warning = len(active_view[active_view["COI Status"] == "Warning"])
critical = len(active_view[active_view["COI Status"].isin(["Critical", "Expired", "No COI"])])

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f'<div class="metric-card total"><div class="metric-number" style="color:#3498db">{total}</div><div class="metric-label">Active Vendors</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card valid"><div class="metric-number" style="color:#2ecc71">{valid}</div><div class="metric-label">COI Valid</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card warning"><div class="metric-number" style="color:#f39c12">{warning}</div><div class="metric-label">COI Warning ≤90d</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card critical"><div class="metric-number" style="color:#e74c3c">{critical}</div><div class="metric-label">COI Critical/Expired</div></div>', unsafe_allow_html=True)
with col5:
    inactive = len(view[view["Active"] == False])
    st.markdown(f'<div class="metric-card" style="border-top: 3px solid #555;"><div class="metric-number" style="color:#666">{inactive}</div><div class="metric-label">Inactive</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ALERT BANNER
# ─────────────────────────────────────────────
urgent = active_view[active_view["COI Days Left"] <= 30].sort_values("COI Days Left")
if not urgent.empty:
    st.markdown('<div class="section-header">🚨 Urgent — COI Expiring Within 30 Days</div>', unsafe_allow_html=True)
    for _, row in urgent.iterrows():
        label = "EXPIRED" if row["COI Days Left"] < 0 else f"{row['COI Days Left']}d LEFT"
        color = "#e74c3c" if row["COI Days Left"] < 0 else "#f39c12"
        exp_str = row.get("COI Expiry", "N/A")
        st.markdown(f'<div class="alert-banner"><span style="color:{color};font-weight:700;">[{label}]</span> &nbsp; <span style="color:#ddd;">{row["Vendor"]}</span> &nbsp;·&nbsp; <span style="color:#888;">COI: {exp_str}</span></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 All Vendors", "📊 Analytics", "➕ Add / Edit", "📤 Upload COI PDF", "💬 Notes Feed", "✉️ Email Generator"])

# ── TAB 1: VENDOR TABLE ──────────────────────
with tab1:
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        search = st.text_input("🔍 Search vendor", placeholder="Type name...")
    with col_f2:
        status_filter = st.selectbox("COI Status", ["All", "Valid", "Warning", "Critical", "Expired", "No COI", "Inactive"])
    with col_f3:
        show_inactive = st.checkbox("Show inactive vendors", value=False)

    filtered = view.copy()
    if search:
        filtered = filtered[filtered["Vendor"].str.contains(search, case=False, na=False)]
    if not show_inactive:
        filtered = filtered[filtered["Active"] == True]
    if status_filter != "All":
        if status_filter == "Inactive":
            filtered = filtered[filtered["Active"] == False]
        else:
            filtered = filtered[filtered["COI Status"] == status_filter]

    filtered = filtered.sort_values("COI Days Left", ascending=True)

    st.markdown(f'<div style="font-family: Space Mono, monospace; font-size:11px; color:#666; margin-bottom:8px;">{len(filtered)} vendors shown</div>', unsafe_allow_html=True)

    badge_map = {
        "Valid": "badge-valid", "Warning": "badge-warning",
        "Critical": "badge-critical", "Expired": "badge-expired",
        "Inactive": "badge-inactive", "No COI": "badge-expired", "Unknown": "badge-inactive"
    }

    # Table header
    h1, h2, h3, h4, h5, h6, h7 = st.columns([3, 1.5, 1.5, 1.2, 1.2, 1, 1.5])
    for col, label in zip([h1, h2, h3, h4, h5, h6, h7],
                           ["VENDOR", "COI EXPIRY", "WORKSAFE EXPIRY", "COI STATUS", "WS STATUS", "OHS PLAN", "ACTIONS"]):
        col.markdown(f'<div style="font-family:Space Mono,monospace;font-size:10px;color:#555;letter-spacing:0.12em;padding-bottom:4px;border-bottom:1px solid #2a2f45;">{label}</div>', unsafe_allow_html=True)

    for i, row in filtered.iterrows():
        c1, c2, c3, c4, c5, c6, c7 = st.columns([3, 1.5, 1.5, 1.2, 1.2, 1, 1.5])

        active_dot = "🟢" if row["Active"] else "⚫"
        c1.markdown(f'<div style="font-family:Barlow Condensed,sans-serif;font-size:1em;font-weight:600;padding:6px 0;">{active_dot} {row["Vendor"]}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div style="font-family:Space Mono,monospace;font-size:11px;padding:6px 0;color:#ccc;">{row.get("COI Expiry","") or "—"}</div>', unsafe_allow_html=True)
        c3.markdown(f'<div style="font-family:Space Mono,monospace;font-size:11px;padding:6px 0;color:#ccc;">{row.get("WorkSafe Expiry","") or "—"}</div>', unsafe_allow_html=True)

        coi_cls = badge_map.get(row["COI Status"], "badge-inactive")
        ws_cls = badge_map.get(row["WS Status"], "badge-inactive")
        c4.markdown(f'<div style="padding:6px 0;"><span class="status-badge {coi_cls}">{row["COI Status"]}</span></div>', unsafe_allow_html=True)
        c5.markdown(f'<div style="padding:6px 0;"><span class="status-badge {ws_cls}">{row["WS Status"]}</span></div>', unsafe_allow_html=True)
        c6.markdown(f'<div style="font-size:11px;color:#888;padding:6px 0;">{row.get("OHS Plan","") or "—"}</div>', unsafe_allow_html=True)

        with c7:
            wcb_num = str(row.get("WCB Number", "") or "").strip()
            ws_url = "https://www.worksafebc.com/en/insurance/employer-coverage/clearance-letters"
            ca_col, cb_col = c7.columns(2)
            ca_col.markdown(f'<a href="{ws_url}" target="_blank" style="font-family:Space Mono,monospace;font-size:9px;color:#3498db;text-decoration:none;border:1px solid #3498db;padding:3px 5px;border-radius:2px;">WCB</a>', unsafe_allow_html=True)
            if cb_col.button("✏️", key=f"edit_{i}", help="Edit this vendor"):
                if st.session_state.get("inline_edit") == i:
                    st.session_state.pop("inline_edit")
                else:
                    st.session_state["inline_edit"] = i

        # Inline edit form — appears directly under the row
        if st.session_state.get("inline_edit") == i:
            with st.container():
                st.markdown(f'<div style="background:#1a1e2e;border:1px solid #e05c2a;border-radius:4px;padding:16px;margin:4px 0 10px 0;">', unsafe_allow_html=True)
                st.markdown(f'<div style="font-family:Barlow Condensed,sans-serif;font-weight:600;color:#e05c2a;letter-spacing:0.1em;margin-bottom:10px;">EDITING: {row["Vendor"]}</div>', unsafe_allow_html=True)
                with st.form(key=f"inline_form_{i}"):
                    ie1, ie2, ie3 = st.columns(3)
                    with ie1:
                        ie_vendor = st.text_input("Vendor Name", value=str(row.get("Vendor", "")))
                        ie_email  = st.text_input("Email", value=str(row.get("Email", "") or ""))
                        ie_wcb    = st.text_input("WCB Number", value=str(row.get("WCB Number", "") or ""))
                    with ie2:
                        try:
                            ie_coi = st.date_input("COI Expiry", value=pd.to_datetime(row.get("COI Expiry")).date() if row.get("COI Expiry") else date.today())
                        except:
                            ie_coi = st.date_input("COI Expiry", value=date.today())
                        try:
                            ie_ws = st.date_input("WorkSafe Expiry", value=pd.to_datetime(row.get("WorkSafe Expiry")).date() if row.get("WorkSafe Expiry") else date.today())
                        except:
                            ie_ws = st.date_input("WorkSafe Expiry", value=date.today())
                    with ie3:
                        ie_ohs = st.selectbox("OHS Plan", ["", "Yes", "Electronic", "N/A"],
                            index=["", "Yes", "Electronic", "N/A"].index(row.get("OHS Plan", "")) if row.get("OHS Plan", "") in ["", "Yes", "Electronic", "N/A"] else 0)
                        ie_active = st.checkbox("Active", value=bool(row.get("Active", True)))
                        ie_notes = st.text_input("Notes", value=str(row.get("Notes", "") or ""))
                    fs_col, fc_col = st.columns([1, 1])
                    with fs_col:
                        ie_save = st.form_submit_button("💾 Save")
                    with fc_col:
                        ie_cancel = st.form_submit_button("✕ Cancel")
                    if ie_save:
                        for col in ["Vendor","Email","OHS Plan","COI Expiry","WorkSafe Expiry","Active","Notes","WCB Number"]:
                            df[col] = df[col].astype(object)
                        df.at[i, "Vendor"]       = ie_vendor
                        df.at[i, "Email"]        = ie_email
                        df.at[i, "WCB Number"]   = ie_wcb
                        df.at[i, "OHS Plan"]     = ie_ohs
                        df.at[i, "COI Expiry"]   = ie_coi.strftime("%Y-%m-%d")
                        df.at[i, "WorkSafe Expiry"] = ie_ws.strftime("%Y-%m-%d")
                        df.at[i, "Active"]       = ie_active
                        df.at[i, "Notes"]        = ie_notes
                        save_data(df)
                        st.session_state.pop("inline_edit", None)
                        st.success("Saved!")
                        st.rerun()
                    if ie_cancel:
                        st.session_state.pop("inline_edit", None)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 2: ANALYTICS ─────────────────────────
with tab2:
    active_df = view[view["Active"] == True].copy()

    # COI status breakdown
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-header">COI Status Breakdown</div>', unsafe_allow_html=True)
        status_counts = active_df["COI Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        color_map = {"Valid": "#2ecc71", "Warning": "#f39c12", "Critical": "#e74c3c", "Expired": "#c0392b", "No COI": "#8e44ad", "Unknown": "#555"}
        fig_pie = px.pie(status_counts, values="Count", names="Status",
                         color="Status", color_discrete_map=color_map,
                         hole=0.5)
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ccc", family="Barlow Condensed"),
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-header">WorkSafeBC Status Breakdown</div>', unsafe_allow_html=True)
        ws_counts = active_df["WS Status"].value_counts().reset_index()
        ws_counts.columns = ["Status", "Count"]
        fig_ws = px.pie(ws_counts, values="Count", names="Status",
                        color="Status", color_discrete_map=color_map, hole=0.5)
        fig_ws.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ccc", family="Barlow Condensed"),
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig_ws, use_container_width=True)

    # Expiry Timeline
    st.markdown('<div class="section-header">COI Expiry Timeline</div>', unsafe_allow_html=True)
    timeline_df = active_df[active_df["COI Expiry"].notna() & (active_df["COI Expiry"] != "")].copy()
    timeline_df["COI Expiry dt"] = pd.to_datetime(timeline_df["COI Expiry"], errors="coerce")
    timeline_df = timeline_df.dropna(subset=["COI Expiry dt"]).sort_values("COI Expiry dt")

    fig_tl = px.scatter(
        timeline_df,
        x="COI Expiry dt",
        y="Vendor",
        color="COI Status",
        color_discrete_map=color_map,
        size_max=12,
        hover_data={"COI Days Left": True, "COI Expiry dt": False},
        labels={"COI Expiry dt": "Expiry Date"}
    )
    fig_tl.update_traces(marker=dict(size=10, line=dict(width=1, color="#0f1117")))
    fig_tl.add_vline(x=datetime.today().timestamp() * 1000, line_dash="dash", line_color="#e05c2a", annotation_text="TODAY")
    fig_tl.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(20,24,36,0.8)",
        font=dict(color="#ccc", family="Barlow Condensed"),
        xaxis=dict(gridcolor="#2a2f45", color="#888"),
        yaxis=dict(gridcolor="#2a2f45", color="#888"),
        height=max(400, len(timeline_df) * 18),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    st.plotly_chart(fig_tl, use_container_width=True)

    # Renewals due per month
    st.markdown('<div class="section-header">Upcoming Renewals by Month</div>', unsafe_allow_html=True)
    future = timeline_df[timeline_df["COI Days Left"] >= 0].copy()
    future["Month"] = future["COI Expiry dt"].dt.to_period("M").astype(str)
    monthly = future.groupby("Month").size().reset_index(name="Count").sort_values("Month")
    fig_bar = px.bar(monthly, x="Month", y="Count", color_discrete_sequence=["#e05c2a"])
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(20,24,36,0.8)",
        font=dict(color="#ccc", family="Barlow Condensed"),
        xaxis=dict(gridcolor="#2a2f45", color="#888"),
        yaxis=dict(gridcolor="#2a2f45", color="#888"),
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── TAB 3: ADD / EDIT ─────────────────────────
with tab3:
    st.markdown('<div class="section-header">Add New Vendor</div>', unsafe_allow_html=True)

    with st.form("add_vendor_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_vendor = st.text_input("Vendor Name *")
            new_email = st.text_input("Email")
            new_ohs = st.selectbox("OHS Plan", ["", "Yes", "Electronic", "N/A"])
        with col2:
            new_coi = st.date_input("COI Expiry Date")
            new_ws = st.date_input("WorkSafeBC Clearance Expiry")
            new_active = st.checkbox("Active Contractor", value=True)
        new_wcb_num = st.text_input("WCB Account Number")
        new_notes = st.text_input("Notes")

        submitted = st.form_submit_button("💾 Add Vendor")
        if submitted:
            if new_vendor:
                new_row = {
                    "Vendor": new_vendor,
                    "COI Expiry": new_coi.strftime("%Y-%m-%d"),
                    "WorkSafe Expiry": new_ws.strftime("%Y-%m-%d"),
                    "OHS Plan": new_ohs,
                    "Active": new_active,
                    "Email": new_email,
                    "Notes": new_notes,
                    "WCB Number": "",
                    "File": ""
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success(f"✅ {new_vendor} added successfully")
                st.rerun()
            else:
                st.error("Vendor name is required")

    st.markdown('<div class="section-header" style="margin-top:32px;">Edit / Delete Existing Vendor</div>', unsafe_allow_html=True)

    vendor_names = df["Vendor"].tolist()
    default_vendor = st.session_state.get("selected_vendor_edit", "— Select —")
    default_idx = (["— Select —"] + vendor_names).index(default_vendor) if default_vendor in vendor_names else 0
    selected_vendor = st.selectbox("Select vendor to edit", ["— Select —"] + vendor_names, index=default_idx)

    if selected_vendor != "— Select —":
        idx = df[df["Vendor"] == selected_vendor].index[0]
        row = df.loc[idx]

        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                e_vendor = st.text_input("Vendor Name", value=row.get("Vendor", ""))
                e_email  = st.text_input("Email", value=row.get("Email", ""))
                e_wcb    = st.text_input("WCB Account Number", value=str(row.get("WCB Number", "") or ""), placeholder="e.g. 123456")
                e_ohs    = st.selectbox("OHS Plan", ["", "Yes", "Electronic", "N/A"],
                                         index=["", "Yes", "Electronic", "N/A"].index(row.get("OHS Plan", "")) if row.get("OHS Plan", "") in ["", "Yes", "Electronic", "N/A"] else 0)
            with col2:
                try:
                    e_coi = st.date_input("COI Expiry", value=pd.to_datetime(row.get("COI Expiry")).date() if row.get("COI Expiry") else date.today())
                except:
                    e_coi = st.date_input("COI Expiry", value=date.today())
                try:
                    e_ws = st.date_input("WorkSafe Expiry", value=pd.to_datetime(row.get("WorkSafe Expiry")).date() if row.get("WorkSafe Expiry") else date.today())
                except:
                    e_ws = st.date_input("WorkSafe Expiry", value=date.today())
                e_active = st.checkbox("Active", value=bool(row.get("Active", True)))
            e_notes = st.text_input("Notes", value=str(row.get("Notes", "") or ""))

            col_save, col_del = st.columns([1, 1])
            with col_save:
                save_edit = st.form_submit_button("💾 Save Changes")
            with col_del:
                del_btn = st.form_submit_button("🗑️ Delete Vendor", type="secondary")

            if save_edit:
                for col in ["Vendor", "Email", "OHS Plan", "COI Expiry", "WorkSafe Expiry", "Active", "Notes", "WCB Number"]:
                    df[col] = df[col].astype(object)
                df.at[idx, "Vendor"] = e_vendor
                df.at[idx, "Email"] = e_email
                df.at[idx, "WCB Number"] = e_wcb
                df.at[idx, "OHS Plan"] = e_ohs
                df.at[idx, "COI Expiry"] = e_coi.strftime("%Y-%m-%d")
                df.at[idx, "WorkSafe Expiry"] = e_ws.strftime("%Y-%m-%d")
                df.at[idx, "Active"] = e_active
                df.at[idx, "Notes"] = e_notes
                save_data(df)
                st.success("Changes saved")
                if "edit_vendor_name" in st.session_state:
                    del st.session_state["edit_vendor_name"]
                st.rerun()

            if del_btn:
                file_path = df.at[idx, "File"]
                if file_path and os.path.exists(str(file_path)):
                    os.remove(file_path)
                df = df.drop(idx).reset_index(drop=True)
                save_data(df)
                st.success(f"{selected_vendor} deleted")
                st.rerun()

# ── TAB 4: PDF UPLOAD ─────────────────────────
with tab4:
    st.markdown('<div class="section-header">Upload Certificate of Insurance PDF</div>', unsafe_allow_html=True)
    st.info("Text-based PDFs only. Scanned/image PDFs are not supported without OCR.")

    file = st.file_uploader("Select COI PDF", type=["pdf"])

    if file:
        file_path = os.path.join(UPLOAD_FOLDER, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())

        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    pt = page.extract_text()
                    if pt:
                        text += pt + "\n"
        except Exception as e:
            st.error(f"PDF read error: {e}")

        if text:
            st.text_area("Extracted Text (preview)", text[:2000], height=200)

            # Auto-detect expiry
            def find_expiry(text):
                lines = text.split("\n")
                for line in lines:
                    if any(k in line.lower() for k in ["expiry", "expiration", "expires"]):
                        dates = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", line)
                        for d in dates:
                            try:
                                import dateparser
                                p = dateparser.parse(d)
                                if p:
                                    return p.date()
                            except:
                                pass
                return None

            detected = find_expiry(text)
            if detected:
                st.success(f"Detected expiry: {detected}")

        col1, col2 = st.columns(2)
        with col1:
            vendor_names = ["— New vendor —"] + df["Vendor"].tolist()
            sel = st.selectbox("Link to vendor", vendor_names)
        with col2:
            if detected:
                expiry_input = st.date_input("COI Expiry Date", value=detected)
            else:
                expiry_input = st.date_input("COI Expiry Date")

        if st.button("💾 Save PDF & Update Record"):
            if sel == "— New vendor —":
                st.warning("Please select an existing vendor or add them first in the Add/Edit tab")
            else:
                idx = df[df["Vendor"] == sel].index[0]
                df.at[idx, "COI Expiry"] = expiry_input.strftime("%Y-%m-%d")
                df.at[idx, "File"] = file_path
                save_data(df)
                st.success(f"COI updated for {sel}")
                st.rerun()


# ── TAB 5: NOTES FEED ────────────────────────
with tab5:
    st.markdown('<div class="section-header">Vendor Notes & Comments Feed</div>', unsafe_allow_html=True)

    all_notes = load_notes()
    vendor_list = df["Vendor"].sort_values().tolist()

    col_n1, col_n2 = st.columns([2, 3])

    with col_n1:
        note_vendor = st.selectbox("Select Vendor", vendor_list, key="note_vendor_sel")
        note_author = st.text_input("Your name", value="Facilities", key="note_author")
        note_text = st.text_area("Add a note", height=100, key="note_text_input", placeholder="e.g. Called vendor — renewal submitted, expect COI by end of month.")
        if st.button("💬 Post Note"):
            if note_text.strip():
                add_note(note_vendor, note_text.strip(), note_author.strip() or "Facilities")
                st.success("Note added")
                st.rerun()
            else:
                st.warning("Note cannot be empty")

    with col_n2:
        if note_vendor and note_vendor in all_notes and all_notes[note_vendor]:
            st.markdown(f'<div style="font-family:Barlow Condensed,sans-serif;font-size:1em;font-weight:600;letter-spacing:0.1em;color:#e05c2a;margin-bottom:10px;">{note_vendor}</div>', unsafe_allow_html=True)
            for entry in all_notes[note_vendor]:
                st.markdown(f"""
                <div style="background:#141824;border-left:3px solid #e05c2a;padding:10px 14px;margin-bottom:8px;border-radius:0 3px 3px 0;">
                    <div style="font-family:Space Mono,monospace;font-size:10px;color:#555;margin-bottom:4px;">{entry['ts']} · {entry['author']}</div>
                    <div style="font-family:Barlow Condensed,sans-serif;font-size:1em;color:#ddd;">{entry['text']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#555;font-family:Space Mono,monospace;font-size:12px;margin-top:20px;">No notes yet for this vendor.</div>', unsafe_allow_html=True)

    # All recent notes across all vendors
    st.markdown('<div class="section-header" style="margin-top:28px;">Recent Activity — All Vendors</div>', unsafe_allow_html=True)
    all_entries = []
    for vendor, entries in all_notes.items():
        for e in entries:
            all_entries.append({"vendor": vendor, **e})
    if all_entries:
        all_entries.sort(key=lambda x: x["ts"], reverse=True)
        for entry in all_entries[:20]:
            st.markdown(f"""
            <div style="background:#141824;border:1px solid #2a2f45;padding:8px 14px;margin-bottom:5px;border-radius:3px;display:flex;gap:12px;align-items:baseline;">
                <span style="font-family:Barlow Condensed,sans-serif;font-weight:600;color:#e05c2a;min-width:200px;">{entry['vendor']}</span>
                <span style="font-family:Barlow Condensed,sans-serif;color:#ddd;flex:1;">{entry['text']}</span>
                <span style="font-family:Space Mono,monospace;font-size:10px;color:#555;white-space:nowrap;">{entry['ts']} · {entry['author']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No notes posted yet across any vendor.")


# ── TAB 6: EMAIL GENERATOR ───────────────────
with tab6:
    st.markdown('<div class="section-header">Email Renewal Request Generator</div>', unsafe_allow_html=True)

    view_email = build_view(df)
    active_email = view_email[view_email["Active"] == True]

    col_e1, col_e2 = st.columns([1, 2])

    with col_e1:
        st.markdown('<div style="font-family:Space Mono,monospace;font-size:11px;color:#888;margin-bottom:8px;">SELECT VENDORS TO CONTACT</div>', unsafe_allow_html=True)

        email_filter = st.selectbox("Filter by status", ["All Active", "Expired", "Critical (≤30d)", "Warning (≤90d)", "No COI"], key="email_filter")

        if email_filter == "Expired":
            email_pool = active_email[active_email["COI Status"] == "Expired"]
        elif email_filter == "Critical (≤30d)":
            email_pool = active_email[active_email["COI Status"].isin(["Critical", "Expired"])]
        elif email_filter == "Warning (≤90d)":
            email_pool = active_email[active_email["COI Status"].isin(["Warning", "Critical", "Expired"])]
        elif email_filter == "No COI":
            email_pool = active_email[active_email["COI Status"] == "No COI"]
        else:
            email_pool = active_email

        selected_vendors = st.multiselect(
            "Vendors to include",
            email_pool["Vendor"].tolist(),
            default=email_pool[email_pool["COI Status"].isin(["Expired", "Critical"])]["Vendor"].tolist()[:5],
            key="email_vendors"
        )

        sender_name = st.text_input("Your name", value="Fabien Astre", key="email_sender")
        sender_title = st.text_input("Your title", value="Facilities & Engineering Manager", key="email_title")
        property_name = st.text_input("Property", value="Aberdeen Mall", key="email_property")
        urgency = st.selectbox("Tone", ["Standard", "Urgent", "Final Notice"], key="email_tone")

    with col_e2:
        if selected_vendors:
            for vendor in selected_vendors:
                vrow = view_email[view_email["Vendor"] == vendor].iloc[0]
                email_addr = vrow.get("Email", "") or ""
                coi_exp = vrow.get("COI Expiry", "") or "not on file"
                days_left = int(vrow["COI Days Left"]) if vrow["COI Days Left"] not in [9999, -9999] else None
                status = vrow["COI Status"]

                if status == "Expired":
                    subject = f"URGENT: Expired Certificate of Insurance — {vendor}"
                    status_line = f"our records show your Certificate of Insurance expired on {coi_exp}"
                    action_line = "we require an updated COI immediately to continue work on the property"
                elif status in ["Critical"]:
                    subject = f"ACTION REQUIRED: COI Renewal Required — {vendor}"
                    status_line = f"your Certificate of Insurance is set to expire on {coi_exp} ({days_left} days)"
                    action_line = f"please provide a renewed COI before {coi_exp} to avoid any interruption to your contractor status"
                elif urgency == "Final Notice":
                    subject = f"FINAL NOTICE: Certificate of Insurance Renewal — {vendor}"
                    status_line = f"your Certificate of Insurance expires on {coi_exp}"
                    action_line = "this is our final notice — failure to provide an updated COI will result in suspension of contractor access"
                else:
                    subject = f"Certificate of Insurance Renewal — {vendor}"
                    status_line = f"your Certificate of Insurance is scheduled to expire on {coi_exp}"
                    action_line = "please arrange renewal and forward the updated certificate at your earliest convenience"

                email_body = f"""Subject: {subject}

To: {email_addr or '[vendor email]'}

Dear {vendor} Team,

I hope this message finds you well. I am writing to inform you that {status_line} on file with {property_name}.

As part of our ongoing contractor compliance program, {action_line}. Please ensure the certificate names {property_name} as an additional insured and meets our minimum coverage requirements.

Required documentation:
  • Certificate of Insurance (minimum $2M general liability)
  • WorkSafeBC Clearance Letter (if applicable)

Please forward the updated documents to this email or contact me directly if you have any questions.

Thank you for your continued partnership with {property_name}.

Best regards,
{sender_name}
{sender_title}
{property_name}"""

                st.markdown(f'<div style="font-family:Barlow Condensed,sans-serif;font-weight:600;color:#e05c2a;letter-spacing:0.1em;margin:16px 0 6px 0;">{vendor} <span style="font-size:0.8em;color:#666;">— {status}</span></div>', unsafe_allow_html=True)
                st.text_area("", value=email_body, height=320, key=f"email_{vendor}")
                st.markdown("<hr style='border-color:#2a2f45;margin:8px 0;'>", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#555;font-family:Space Mono,monospace;font-size:12px;margin-top:40px;text-align:center;">← Select vendors on the left to generate renewal emails</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div style="border-top:1px solid #2a2f45; margin-top:32px; padding-top:12px; font-family:Space Mono,monospace; font-size:10px; color:#444; text-align:center;">
    ABERDEEN MALL — FACILITIES & ENGINEERING · COI COMPLIANCE TRACKER
</div>
""", unsafe_allow_html=True)
