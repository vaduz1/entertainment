import streamlit as st
import serial
import imaplib
import email
import re
import os

# --- Helper Functions ---
def get_sim_codes():
    try:
        # Common port for SIM HATs on Raspberry Pi
        ser = serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=2)
        ser.write(b'AT+CMGF=1\r\n') # SMS text mode
        ser.write(b'AT+CMGL="ALL"\r\n') # List all messages
        response = ser.read(2048).decode()
        return response
    except Exception as e:
        return f"SIM HAT Error: {e}"

def get_email_codes():
    try:
        # Example for Gmail; use App Passwords if 2FA is on
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        mail.select("inbox")
        
        # Search for recent emails from specific services
        senders = ['netflix', 'disney', 'paramount']
        codes = []
        for sender in senders:
            status, messages = mail.search(None, f'FROM "{sender}"')
            for num in messages[0].split()[-3:]: # Get last 3
                _, msg_data = mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                body = str(msg.get_payload())
                # Extract 6-digit code
                code_match = re.search(r'\b\d{6}\b', body)
                if code_match:
                    codes.append(f"{sender.capitalize()}: {code_match.group(0)}")
        mail.logout()
        return codes if codes else ["No codes found."]
    except Exception as e:
        return [f"Email Error: {e}"]

# --- Streamlit UI ---
st.title("Streamline Service Dashboard")
tab1, tab2, tab3 = st.tabs(["Verification Codes", "Running Services", "Football Channels"])

with tab1:
    st.header("Latest Codes")
    if st.button("Refresh Codes"):
        st.subheader("SIM HAT SMS")
        st.text(get_sim_codes())
        st.subheader("Email Verification (6-Digit)")
        for code in get_email_codes():
            st.write(code)

with tab2:
    st.header("Running Services")
    try:
        with open("services.txt", "r") as f:
            services = f.readlines()
            for svc in services:
                st.write(f"✅ {svc.strip()}")
    except FileNotFoundError:
        st.error("services.txt not found.")

with tab3:
    st.header("Live Football Channels (2025/26)")
    # Sourced from UK/US broadcast data
    st.markdown("""

    | Competition | UK Broadcasters | US Broadcasters |
    | :--- | :--- | :--- |
    | **Premier League** | Sky Sports, TNT Sports | NBC, USA Network, Peacock |
    | **Champions League** | TNT Sports, Amazon Prime | Paramount+, CBS Sports |
    | **Bundesliga** | Sky Sports, BBC Sport | ESPN+ |
    """)

