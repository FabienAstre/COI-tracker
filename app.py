import streamlit as st
import pandas as pd
import pdfplumber
import os
from datetime import datetime
import re
import dateparser
import plotly.express as px

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DATA_FILE = "data.csv"
UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

st.set_page_config(layout="wide")
st.title("📄 COI Compliance Tracker")

# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=[
            "Vendor", "Email", "Policy Type", "Expiry Date", "File"
        ])
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# ─────────────────────────────────────────────
# PDF TEXT EXTRACTION
# ─────────────────────────────────────────────
def extract_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_expiry(text):
    lines = text.split("\n")
    keywords = ["expiry", "expiration", "expires"]

    for line in lines:
        if any(k in line.lower() for k in keywords):
            dates = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", line)
            for d in dates:
                parsed = dateparser.parse(d)
                if parsed:
                    return parsed.date()

    dates = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text)
    for d in dates:
        parsed = dateparser.parse(d)
        if parsed:
            return parsed.date()

    return None

# ─────────────────────────────────────────────
# UPLOAD SECTION
# ─────────────────────────────────────────────
st.subheader("📤 Upload COI PDF")

file = st.file_uploader("Upload Certificate of Insurance", type=["pdf"])

if file:
    filepath = os.path.join(UPLOAD_FOLDER, file.name)

    with open(filepath, "wb") as f:
        f.write(file.getbuffer())

    text = extract_text(filepath)
    expiry = extract_expiry(text)

    st.text_area("PDF Preview", text[:1200], height=200)

    vendor = st.text_input("Vendor")
    email = st.text_input("Email (optional)")
    policy = st.text_input("Policy Type")

    if expiry:
        st.info(f"Detected expiry date: {expiry}")
        expiry_input = st.date_input("Confirm Expiry Date", value=expiry)
    else:
        expiry_input = st.date_input("Enter Expiry Date")

    if st.button("💾 Save COI"):
        new_row = {
            "Vendor": vendor,
            "Email": email,
            "Policy Type": policy,
            "Expiry Date": expiry_input.strftime("%Y-%m-%d"),
            "File": filepath
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)

        st.success("COI saved successfully")

# ─────────────────────────────────────────────
# STATUS ENGINE
# ─────────────────────────────────────────────
def build_timeline(df):
    df = df.copy()

    df["Expiry Date"] = pd.to_datetime(df["Expiry Date"])
    df["Days Left"] = (df["Expiry Date"] - datetime.today()).dt.days

    def status(d):
        if d < 0:
            return "Expired"
        elif d < 7:
            return "Critical"
        elif d < 30:
            return "Warning"
        else:
            return "Valid"

    df["Status"] = df["Days Left"].apply(status)
    return df

# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
st.subheader("📊 Dashboard")

if not df.empty:
    df_view = build_timeline(df)
    st.dataframe(df_view, use_container_width=True)
else:
    st.info("No COIs yet")

# ─────────────────────────────────────────────
# TIMELINE VIEW (CALENDAR STYLE)
# ─────────────────────────────────────────────
st.subheader("📅 Compliance Timeline View")

if not df.empty:
    timeline_df = build_timeline(df)

    fig = px.scatter(
        timeline_df,
        x="Expiry Date",
        y="Vendor",
        color="Status",
        hover_data=["Policy Type", "Days Left"],
        title="COI Expiry Timeline"
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for timeline")

# ─────────────────────────────────────────────
# WEEKLY RISK PANEL
# ─────────────────────────────────────────────
st.subheader("🚨 This Week's Compliance Risks")

if not df.empty:
    df_check = build_timeline(df)
    upcoming = df_check[df_check["Days Left"] <= 7].sort_values("Days Left")

    if not upcoming.empty:
        for _, row in upcoming.iterrows():
            st.error(
                f"⚠️ {row['Vendor']} | {row['Policy Type']} | "
                f"Expires {row['Expiry Date'].date()} "
                f"({row['Days Left']} days left)"
            )
    else:
        st.success("No urgent compliance issues")
