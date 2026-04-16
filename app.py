import streamlit as st
import pandas as pd
import pdfplumber
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import re
import dateparser

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

DATA_FILE = "data.csv"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=[
            "Vendor", "Email", "Policy Type", "Expiry Date",
            "File", "Last Reminder Sent"
        ])
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def send_email(to_email, subject, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(e)
        return False

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

def run_reminders(df):
    today = datetime.today()

    for i, row in df.iterrows():
        expiry = datetime.strptime(row["Expiry Date"], "%Y-%m-%d")
        days_left = (expiry - today).days

        if days_left in [30, 7, 1]:
            if row["Last Reminder Sent"] == str(today.date()):
                continue

            msg = f"COI Expiry Reminder\nVendor: {row['Vendor']}\nExpiry: {row['Expiry Date']}\nDays left: {days_left}"

            if send_email(row["Email"], "COI Reminder", msg):
                df.at[i, "Last Reminder Sent"] = str(today.date())

    save_data(df)

st.title("COI Tracker (No AI)")

df = load_data()

st.subheader("Upload COI")
file = st.file_uploader("Upload PDF", type=["pdf"])

if file:
    filepath = os.path.join(UPLOAD_FOLDER, file.name)
    with open(filepath, "wb") as f:
        f.write(file.getbuffer())

    text = extract_text(filepath)
    expiry = extract_expiry(text)

    st.text_area("Preview", text[:1000])

    vendor = st.text_input("Vendor")
    email = st.text_input("Email")
    policy = st.text_input("Policy Type")

    if expiry:
        st.info(f"Detected expiry: {expiry}")
        expiry_input = st.date_input("Confirm expiry", value=expiry)
    else:
        expiry_input = st.date_input("Enter expiry")

    if st.button("Save"):
        new_row = {
            "Vendor": vendor,
            "Email": email,
            "Policy Type": policy,
            "Expiry Date": expiry_input.strftime("%Y-%m-%d"),
            "File": filepath,
            "Last Reminder Sent": ""
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("Saved")

st.subheader("Dashboard")

if not df.empty:
    df["Expiry Date"] = pd.to_datetime(df["Expiry Date"])
    df["Days Left"] = (df["Expiry Date"] - datetime.today()).dt.days
    st.dataframe(df)

if st.button("Run Reminders"):
    run_reminders(df)
    st.success("Reminders sent")
