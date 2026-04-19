import streamlit as st
import serial
import imaplib
import email
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = os.getenv("IMAP_SERVER")
SERVICES_LIST = ['ChatGPT', 'Netflix', 'Disney', 'Paramount']

# --- Helper Functions ---

def get_latest_sim_message():
    """Reads only the very last SMS message from the SIM HAT."""
    try:
        with serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=2) as ser:
            ser.write(b'AT+CMGF=1\r\n') 
            ser.write(b'AT+CMGL="ALL"\r\n') 
            response = ser.read(4096).decode(errors='ignore')
            
            # Find all messages
            messages = re.findall(r'\+CMGL:.*?\r\n(.*?)(?=\r\n\+CMGL:|\r\n\r\nOK)', response, re.DOTALL)
            
            # Return only the last one, or a 'not found' string
            return messages[-1].strip() if messages else "No SMS messages found."
    except Exception as e:
        return f"SIM HAT Error: {e}"

def extract_body(msg):
    """Extracts text from email parts."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors='ignore')
    return msg.get_payload(decode=True).decode(errors='ignore')

def get_email_codes():
    """Extracts 6-digit codes from IMAP inbox."""
    if not all([EMAIL_USER, EMAIL_PASS, IMAP_SERVER]):
        return ["Error: Credentials missing."]
    
    extracted_codes = []
    try:
        with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")
            for service in SERVICES_LIST:
                status, data = mail.search(None, f'(OR FROM "{service}" BODY "{service}")')
                if status != 'OK': continue
                mail_ids = data[0].split()[-1:] # Only look at the latest email per service
                for m_id in mail_ids:
                    _, msg_data = mail.fetch(m_id, '(RFC822)')
                    for part in msg_data:
                        if isinstance(part, tuple):
                            msg = email.message_from_bytes(part[1])
                            body = extract_body(msg)
                            match = re.search(r'\b\d{6}\b', body)
                            if match: extracted_codes.append(f"{service}: {match.group(0)}")
        return extracted_codes or ["No codes found."]
    except Exception as e:
        return [f"Email Error: {e}"]

def get_livesoccer_games():
    """Fetches the latest email from livesoccertv.com."""
    try:
        with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")
            status, data = mail.search(None, '(FROM "livesoccertv.com")')
            if status == 'OK' and data[0]:
                latest_id = data[0].split()[-1]
                _, msg_data = mail.fetch(latest_id, '(RFC822)')
                for part in msg_data:
                    if isinstance(part, tuple):
                        msg = email.message_from_bytes(part[1])
                        return extract_body(msg)
            return "No recent LiveSoccerTV emails found."
    except Exception as e:
        return f"Error: {e}"

# --- Streamlit UI ---

st.set_page_config(page_title="Streamline Hub", layout="wide")
st.title("📺 Entertainment Service Dashboard")

tabs = st.tabs(["🔐 Verification", "⚙️ Services", "⚽ Football", "🎮 Games on TV", "✍️ Feedback"])

# Tab 0: Verification (SMS & OTP)
with tabs[0]:
    st.header("Latest OTP & SMS")
    if st.button("Refresh Messages"):
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Last SIM SMS")
            st.info(get_latest_sim_message())
        with c2:
            st.subheader("Email OTPs")
            for code in get_email_codes(): st.success(code)

# Tab 1: Services
with tabs[1]:
    st.header("Current System Services")
    if os.path.exists("services.txt"):
        with open("services.txt", "r") as f:
            for line in f: st.write(f"🟢 {line.strip()}")
    else:
        st.error("services.txt not found.")

# Tab 2: Football Ref
with tabs[2]:
    st.header("Live Sports Broadcasts")
    st.table({
        "Competition": ["Premier League", "Champions League", "Bundesliga"],
        "UK": ["Sky, TNT", "TNT, Amazon", "Sky Sports"],
        "US": ["NBC, Peacock", "Paramount+", "ESPN+"],
        "New Europe": ["Setanta Moldova", "Setanta Georgia", "Setanta Lithuania"]
    })

# Tab 3: Games on TV
with tabs[3]:
    st.header("LiveSoccerTV Schedule")
    if st.button("Fetch Games"):
        st.text_area("Latest Email Content", get_livesoccer_games(), height=400)

# Tab 4: Feedback (UI Only)
with tabs[4]:
    st.header("User Feedback")
    user_feedback = st.text_area("Tell us what you think:", placeholder="Enter your comments here...")
    if st.button("Send Feedback"):
        if user_feedback:
            st.toast("Feedback received! (Demo Mode)", icon="✅")
        else:
            st.warning("Please enter some text first.")
