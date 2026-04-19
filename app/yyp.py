import streamlit as st
import serial
import imaplib
import email
import re
import os
from email.header import decode_header
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration Constants ---
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = os.getenv("IMAP_SERVER")
SERVICES_LIST = ['ChatGPT', 'Netflix', 'Disney', 'Paramount']

# --- Helper Functions ---

def get_sim_messages():
    """Reads SMS content from SIM HAT."""
    try:
        with serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=2) as ser:
            ser.write(b'AT+CMGF=1\r\n') 
            ser.write(b'AT+CMGL="ALL"\r\n') 
            response = ser.read(4096).decode(errors='ignore')
            
            # Extract message bodies between +CMGL headers and OK
            messages = re.findall(r'\+CMGL:.*?\r\n(.*?)(?=\r\n\+CMGL:|\r\n\r\nOK)', response, re.DOTALL)
            return [msg.strip() for msg in messages] if messages else ["No SMS messages found."]
    except Exception as e:
        return [f"SIM HAT Error: {e}"]

def extract_body(msg):
    """Helper to extract text from email parts."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors='ignore')
    return msg.get_payload(decode=True).decode(errors='ignore')

def get_email_codes():
    """Extracts 6-digit codes from IMAP inbox."""
    if not all([EMAIL_USER, EMAIL_PASS, IMAP_SERVER]):
        return ["Error: Missing credentials in .env file."]

    extracted_codes = []
    try:
        with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")
            
            for service in SERVICES_LIST:
                # Search for service name in sender or body
                status, data = mail.search(None, f'(OR FROM "{service}" BODY "{service}")')
                if status != 'OK': continue

                # Get IDs of last 2 emails
                mail_ids = data[0].split()[-2:]
                for m_id in mail_ids:
                    _, msg_data = mail.fetch(m_id, '(RFC822)')
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            body = extract_body(msg)
                            code_match = re.search(r'\b\d{6}\b', body)
                            if code_match:
                                extracted_codes.append(f"{service}: {code_match.group(0)}")
        
        return extracted_codes or ["No codes found in recent emails."]
    except Exception as e:
        return [f"Email Error: {e}"]

# --- Streamlit UI ---

st.set_page_config(page_title="Streamline Hub", layout="wide")
st.title("📺 Streamline Service Dashboard")

tabs = st.tabs(["🔐 Verification", "⚙️ Services", "⚽ Football", "Games", "Feedback"])

with tabs[0]:
    st.header("Latest OTP & Verification")
    if st.button("Refresh All Codes"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("SIM HAT SMS")
            for msg in get_sim_messages(): st.info(msg)
        with col2:
            st.subheader("Email OTPs")
            for code in get_email_codes(): st.success(code)

with tabs[1]:
    st.header("Current System Services")
    if os.path.exists("services.txt"):
        with open("services.txt", "r") as f:
            lines = f.readlines()
            for line in lines: st.write(f"🟢 {line.strip()}")
    else:
        st.error("services.txt not found.")

with tabs[2]:
    st.header("Live Sports Broadcasts")
    st.table({
        "Competition": ["Premier League", "Champions League", "Bundesliga"],
        "UK": ["Sky, TNT", "TNT, Amazon", "Sky Sports"],
        "US": ["NBC, Peacock", "Paramount+", "ESPN+"],
        "New Europe": ["Setanta Moldova", "Setanta Georgia", "Setanta Lithuania"]
    })
