import streamlit as st
import serial
import imaplib
import email
import re
import os
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# --- Configuration ---
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = os.getenv("IMAP_SERVER")
SERVICES_LIST = ['ChatGPT', 'Netflix', 'Paramount', 'Discovery', 'HBO Max Code', 'MEGOGO' , 'SKY', 'Disney', 'Roborock']

# --- Helper Functions ---

def get_latest_sim_message():
    """Reads only the very last SMS message from the SIM HAT."""
    try:
        with serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=2) as ser:
            ser.write(b'AT+CMGF=1\r\n') 
            ser.write(b'AT+CMGL="ALL"\r\n') 
            response = ser.read(4096).decode(errors='ignore')
            # Extracting all message bodies
            messages = re.findall(r'\+CMGL:.*?\r\n(.*?)(?=\r\n\+CMGL:|\r\n\r\nOK)', response, re.DOTALL)
            return messages[-1].strip() if messages else "No SMS messages found."
    except Exception as e:
        return f"SIM HAT Error: {e}"

def extract_body(msg):
    """Extracts plain text body from email, bypassing HTML tags."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors='ignore')
    return msg.get_payload(decode=True).decode(errors='ignore')

def get_email_codes(pause_seconds=5):
    """Extracts codes using service-specific regex from .env and a 500-char window."""
    if not all([EMAIL_USER, EMAIL_PASS, IMAP_SERVER]):
        return ["Error: Credentials missing in .env"]
    
    extracted_codes = []
    try:
        with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")
            
            for service in SERVICES_LIST:
                time.sleep(pause_seconds)
                status, data = mail.search(None, f'(OR FROM "{service}" BODY "{service}")')
                if status != 'OK' or not data[0]: continue
                
                # Fetch only the most recent email for this service
                latest_id = data[0].split()[-1]
                _, msg_data = mail.fetch(latest_id, '(RFC822)')
                
                for part in msg_data:
                    if isinstance(part, tuple):
                        msg = email.message_from_bytes(part[1])
                        body = extract_body(msg)
                        
                        # Load regex from .env or fallback to generic 6-digit search
                        env_key = f"REGEX_{service.upper()}"
                        #pattern = os.getenv(env_key, r"\b\d{6}\b")
                        pattern = os.getenv(env_key, r"(?<!#)\b\d{6}\b")       
                        # Apply one-liner logic with re.DOTALL to handle newlines in HTML
                        match = re.search(pattern, body, re.DOTALL)
                        if match:
                            # Use capture group if defined, otherwise full match
                            code = match.group(1) if match.groups() else match.group(0)
                            extracted_codes.append(f"{service}: {code}")
                            
        return extracted_codes or ["No codes found in recent emails."]
    except Exception as e:
        return [f"Email Error: {e}"]

#def get_livesoccer_games():
#    """Fetches and trims LiveSoccerTV email to show only match data."""
#    anchor = "LiveSoccerTV.com - 20 years and still kicking!"
#    try:
#        with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
#            mail.login(EMAIL_USER, EMAIL_PASS)
#            mail.select("inbox")
#            status, data = mail.search(None, '(FROM "livesoccertv.com")')
#            if status == 'OK' and data[0]:
#                latest_id = data[0].split()[-1]
#                _, msg_data = mail.fetch(latest_id, '(RFC822)')
#                for part in msg_data:
#                    if isinstance(part, tuple):
#                        msg = email.message_from_bytes(part[1])
#                        body = extract_body(msg)
#                        return body.split(anchor)[-1].strip() if anchor in body else body.strip()
#            return "No LiveSoccerTV emails found."
#    except Exception as e:
#        return f"Error: {e}"

def get_livesoccer_games():
    """Fetches LiveSoccerTV email, strips HTML, and removes match-link noise."""
    anchor = "LiveSoccerTV.com - 20 years and still kicking!"
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
                        raw_body = extract_body(msg) # Assuming your helper handles decoding

                        # 1. Parse HTML and get text
                        soup = BeautifulSoup(raw_body, "html.parser")
                        text = soup.get_text(separator=' ')

                        # 2. Remove URLs inside parentheses: ( https://... )
                        text = re.sub(r'\(\s*https?://\S+\s*\)', '', text)

                        # 3. Remove labels like [International channels]
                        text = re.sub(r'\[.*?\]', '', text)

                        # 4. Clean up whitespace and apply anchor split
                        clean_text = re.sub(r' +', ' ', text).strip()
                        
                        if anchor in clean_text:
                            return clean_text.split(anchor)[-1].strip()
                        return clean_text
            
            return "No LiveSoccerTV emails found."
    except Exception as e:
        return f"Error: {e}"

# --- Streamlit UI Layout ---

st.set_page_config(page_title="Entertainment Hub", layout="wide")
st.title("📺 Entertainment Service Dashboard")

tabs = st.tabs(["🔐 Verification", "⚙️ Services", "⚽ Football", "🎮 Games on TV", "✍️ Feedback"])

# Tab 0: Verification
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

# Tab 1: System Services
with tabs[1]:
    st.header("Current System Services")
    if os.path.exists("services.txt"):
        with open("services.txt", "r") as f:
            for line in f: st.write(f"🟢 {line.strip()}")
    else:
        st.error("services.txt file not found.")

# Tab 2: Football Broadcast Reference
with tabs[2]:
    st.header("Live Sports Broadcasts")
    st.table({
        "Competition": ["Premier League", "Champions League", "Bundesliga", "Seria A"],
        "UK": ["Sky, HBO, TNT", "TNT, Amazon", "Sky Sports", "HBO, TNT"],
        "US": ["NBC, Peacock", "Paramount+", "ESPN+" , ""],
        "New Europe": ["Setanta Moldova", "Setanta Georgia", "Setanta Lithuania" , "Setanta Kaliningrad"]
    })

# Tab 3: Games on TV
with tabs[3]:
    st.header("LiveSoccerTV Schedule")

# Format: [Link Text](URL)
    st.markdown("Visit [LiveSoccerTV Schedule](https://www.livesoccertv.com) for the latest match schedules.")

    if st.button("Fetch Games"):
        st.text_area("Schedule Data", get_livesoccer_games(), height=500)

# Tab 4: Feedback (Demo UI)
with tabs[4]:
    st.header("User Feedback")
    user_feedback = st.text_area("Your Comments:", placeholder="Enter feedback here...")
    if st.button("Send Feedback"):
        if user_feedback:
            st.toast("Feedback received! (Demo Mode)", icon="✅")
        else:
            st.warning("Please enter text before sending.")
