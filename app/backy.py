import streamlit as st
import serial
import imaplib
import email
import re
import os
from dotenv import load_dotenv

# --- Helper Functions ---
def get_sim_messages():
    try:
        # Serial setup for Raspberry Pi SIM HAT
        ser = serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=2)
        ser.write(b'AT+CMGF=1\r\n') 
        ser.write(b'AT+CMGL="ALL"\r\n') 
        response = ser.read(4096).decode()
        
        # Regex to find the message text (the line after the +CMGL header)
        # It ignores the metadata and just grabs the actual SMS content
        messages = re.findall(r'\+CMGL:.*?\r\n(.*?)(?=\r\n\+CMGL:|\r\n\r\nOK)', response, re.DOTALL)
        
        return [msg.strip() for msg in messages] if messages else ["No SMS found."]
    except Exception as e:
        return [f"SIM HAT Error: {e}"]

def get_email_codes():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        mail.select("inbox")
        
        senders = ['netflix', 'disney', 'paramount']
        codes = []
        for sender in senders:
            status, messages = mail.search(None, f'FROM "{sender}"')
            if status == 'OK':
                for num in messages[0].split()[-3:]: # Get last 3
                    _, msg_data = mail.fetch(num, '(RFC822)')
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # Handle multipart or plain text emails
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = str(part.get_payload(decode=True))
                    else:
                        body = str(msg.get_payload(decode=True))

                    code_match = re.search(r'\b\d{6}\b', body)
                    if code_match:
                        codes.append(f"{sender.capitalize()}: {code_match.group(0)}")
        mail.logout()
        return codes if codes else ["No email codes found."]
    except Exception as e:
        return [f"Email Error: {e}"]

# --- Streamlit UI ---
st.title("Streamline Service Dashboard")
tab1, tab2, tab3 = st.tabs(["Verification Codes", "Running Services", "Football Channels"])

with tab1:
    st.header("Latest Codes & Messages")
    if st.button("Refresh All"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("SMS Messages")
            for msg in get_sim_messages():
                st.info(msg)

        with col2:
            st.subheader("Email OTPs (6-Digit)")
            for code in get_email_codes():
                st.success(code)

with tab2:
    st.header("Running Services")
    if os.path.exists("services.txt"):
        with open("services.txt", "r") as f:
            for svc in f.readlines():
                st.write(f"✅ {svc.strip()}")
    else:
        st.error("services.txt not found.")

with tab3:
    st.header("Live Football Channels (2025/26)")
    st.markdown("""

    | Competition | UK Broadcasters | US Broadcasters |
    | :--- | :--- | :--- |
    | **Premier League** | Sky Sports, TNT Sports | NBC, USA Network |
    | **Champions League** | TNT Sports, Amazon Prime | Paramount+, CBS |
    | **Bundesliga** | Sky Sports | ESPN+ |
    """)
