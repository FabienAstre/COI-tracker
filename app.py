import streamlit as st
import pandas as pd
import pdfplumber
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    return text[:12000]

def ai_extract(text):
    prompt = f"""
    Extract vendor name, policy type, expiry date (YYYY-MM-DD), and email from this COI document.
    Return JSON only:
    {{
        "vendor": "",
        "policy_type": "",
        "expiry_date": "",
        "email": ""
    }}
    Document:
    {text}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    try:
        return json.loads(response.choices[0].message.content)
    except:
        return None

def run_reminders(df):
    today = datetime.today()

    for i, row in df.iterrows():
        expiry = datetime.strptime(row["Expiry Date"], "%Y-%m-%d")
        days_left = (expiry - today).days

        if days_left in [30, 7, 1]:
            if row["Last Reminder Sent"] == str(today.date()):
                continue

            msg = f"""
            COI Expiry Reminder

            Vendor: {row['Vendor']}
            Policy: {row['Policy Type']}
            Expiry: {row['Expiry Date']}
            Days left: {days_left}
            """

            if send_email(row["Email"], "COI Expiry Reminder", msg):
                df.at[i, "Last Reminder Sent"] = str(today.date())

    save_data(df)

st.set_page_config(layout="wide")
st.title("AI COI Tracker")

df = load_data()

st.subheader("Upload COI")
file = st.file_uploader("Upload PDF", type=["pdf"])

if file:
    filepath = os.path.join(UPLOAD_FOLDER, file.name)
    with open(filepath, "wb") as f:
        f.write(file.getbuffer())

    with st.spinner("Extracting..."):
        text = extract_text(filepath)
        data = ai_extract(text)

    if data:
        vendor = st.text_input("Vendor", data.get("vendor", ""))
        email = st.text_input("Email", data.get("email", ""))
        policy = st.text_input("Policy Type", data.get("policy_type", ""))
        expiry = st.text_input("Expiry Date (YYYY-MM-DD)", data.get("expiry_date", ""))

        if st.button("Save"):
            new_row = {
                "Vendor": vendor,
                "Email": email,
                "Policy Type": policy,
                "Expiry Date": expiry,
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
    st.success("Done")
