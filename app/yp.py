import streamlit as st
import serial
import imaplib
import email
import re
import os
from email.header import decode_header

# --- Helper Functions ---

def get_sim_messages():
    """Reads SMS only the text message content."""
    try:
        # Serial port for Raspberry Pi SIM HAT (adjust if using /dev/ttyAMA0)
        ser = serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=2)
        ser.write(b'AT+CMGF=1\r\n') 
        ser.write(b'AT+CMGL="ALL"\r\n') 
        response = ser.read(4096).decode(errors='ignore')
        
        # Regex to strip AT headers and metadata, capturing just the message body
        # Looks for the line following +CMGL: and stops before the next +CMGL or OK
        messages = re.findall(r'\+CMGL:.*?\r\n(.*?)(?=\r\n\+CMGL:|\r\n\r\nOK)', response, re.DOTALL)
        
        return [msg.strip() for msg in messages] if messages else ["No SMS messages found."]
    except Exception as e:
        return [f"SIM HAT Error: {e}"]

def get_email_codes():
    """Logs into IMAP and extracts 6-digit codes from specific service emails."""
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    server = os.getenv("IMAP_SERVER")
    if not user or not password:
        return ["Error: Email credentials not found in environment variables."]

    try:
        # Connect to Gmail (standard for most, change if using Outlook/etc)
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("inbox")
        
        services = ['ChatGPT', 'Netflix', 'Disney', 'Paramount']
        extracted_codes = []

        for service in services:
            # Search for the service name in the subject or body for better results
            status, data = mail.search(None, f'(OR FROM "{service}" BODY "{service}")')
            
            if status == 'OK':
                # Get the IDs of the last 2 emails for this service
                mail_ids = data[0].split()[-2:]
                for m_id in mail_ids:
                    _, msg_data = mail.fetch(m_id, '(RFC822)')
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            # Extract body
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode(errors='ignore')
                            else:
                                body = msg.get_payload(decode=True).decode(errors='ignore')

                            # Extract 6-digit code
                            code_match = re.search(r'\b\d{6}\b', body)
                            if code_match:
                                extracted_codes.append(f"{service}: {code_match.group(0)}")
        
        mail.logout()
        return extracted_codes if extracted_codes else ["No verification codes found in recent emails."]
    except Exception as e:
        return [f"Email Connection Error: {e}"]

# --- Streamlit UI Configuration ---

st.set_page_config(page_title="Streamline Hub", layout="wide")
st.title("📺 Streamline Service Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔐 Verification Codes", "⚙️ Running Services", "⚽ Football Channels","Games on TV","Feedback" ])

with tab1:
    st.header("Latest OTP & Verification")
    if st.button("Refresh All Codes"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("SIM HAT SMS Messages")
            for msg in get_sim_messages():
                st.info(msg)

        with col2:
            st.subheader("Email OTPs (6-Digit)")
            for code in get_email_codes():
                st.success(code)

with tab2:
    st.header("Current System Services")
    service_file = "services.txt"
    if os.path.exists(service_file):
        with open(service_file, "r") as f:
            lines = f.readlines()
            if lines:
                for line in lines:
                    st.write(f"🟢 {line.strip()}")
            else:
                st.warning("services.txt is empty.")
    else:
        st.error(f"Configuration Error: '{service_file}' not found.")

with tab3:
    st.header("Live Sports Broadcast Channels")
    st.markdown("""

    | Competition | UK Channels | US Channels | New Europe |
    | :--- | :--- | :--- | :--- |
    | **Premier League** | Sky Sports, TNT Sports | NBC, USA, Peacock | Setanta Moldova |
    | **Champions League** | TNT Sports, Amazon Prime | Paramount+, CBS | Setanta Georgia |
    | **Bundesliga** | Sky Sports | ESPN+ | Setanta Lithuania |
    """)
    st.caption("Broadcast rights valid for the 2025/26 season.")
