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
# DELETE FUNCTION
# ─────────────────────────────────────────────
def delete_coi(index):
    global df

    row = df.iloc[index]

    # delete file if exists
    if "File" in df.columns:
        file_path = row["File"]
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    df = df.drop(index).reset_index(drop=True)
    save_data(df)
    st.rerun()

# ─────────────────────────────────────────────
# PDF EXTRACTION (FIXED)
# ─────────────────────────────────────────────
def extract_text(file):
    text = ""

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"
            else:
                text += f"[Page {page.page_number}: no text detected]\n"

    return text.strip()

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

    st.text_area("📄 PDF Preview", text, height=250)

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
        st.rerun()

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
    view = build_timeline(df)

    st.dataframe(view, use_container_width=True)

    # DELETE BUTTONS
    st.subheader("🗑️ Manage COIs")

    for i, row in view.iterrows():
        col1, col2, col3 = st.columns([3, 3, 1])

        with col1:
            st.write(row["Vendor"])

        with col2:
            st.write(row["Expiry Date"])

        with col3:
            if st.button("Delete", key=f"del_{i}"):
                delete_coi(i)

# ─────────────────────────────────────────────
# TIMELINE VIEW
# ─────────────────────────────────────────────
st.subheader("📅 Compliance Timeline")

if not df.empty:
    timeline = build_timeline(df)

    fig = px.scatter(
        timeline,
        x="Expiry Date",
        y="Vendor",
        color="Status",
        hover_data=["Policy Type", "Days Left"],
        title="COI Expiry Timeline"
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No COIs available")

# ─────────────────────────────────────────────
# WEEKLY RISKS
# ─────────────────────────────────────────────
st.subheader("🚨 Urgent Compliance (≤ 7 days)")

if not df.empty:
    check = build_timeline(df)
    urgent = check[check["Days Left"] <= 7].sort_values("Days Left")

    if not urgent.empty:
        for _, row in urgent.iterrows():
            st.error(
                f"{row['Vendor']} | {row['Policy Type']} | "
                f"{row['Expiry Date'].date()} | {row['Days Left']} days left"
            )
    else:
        st.success("No urgent COIs")
