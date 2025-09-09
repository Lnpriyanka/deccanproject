import streamlit as st
import pandas as pd
import requests
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime

def process_csv_and_fetch_metadata(input_df):
    user_ids = input_df['UID'].unique().tolist()
    wb = Workbook()
    ws = wb.active
    ws.title = "User  Metadata"

    headers = ["User  ID", "Display Name", "First Name", "Last Name", "Email", "Gender", "DOB", "College"]
    ws.append(headers)

    base_url = "https://sso-dev.tpml.in/auth/get-user-metadata?userId="

    for user_id in user_ids:
        url = base_url + str(user_id)
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            metadata = data.get("metadata", {})
            display_name = metadata.get("displayName", "N/A")
            first_name = metadata.get("first_name", "N/A")
            last_name = metadata.get("last_name", "N/A")
            email = metadata.get("dh", {}).get("newsLetter", {}).get("email", "N/A")
            gender = metadata.get("gender", "N/A")
            dob = f'{metadata.get("dob", {}).get("day", "N/A")}-{metadata.get("dob", {}).get("month", "N/A")}-{metadata.get("dob", {}).get("year", "N/A")}'
            college = metadata.get("college", "N/A")

            row = [user_id, display_name, first_name, last_name, email, gender, dob, college]
            ws.append(row)
        else:
            row = [user_id, "Failed to retrieve data", "", "", "", "", "", ""]
            ws.append(row)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

# --- Streamlit UI ---
st.title("User  Metadata Fetcher")

# Initialize session state variables
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'output' not in st.session_state:
    st.session_state.output = None

uploaded_file = st.file_uploader("Upload CSV with UID column", type="csv")

if uploaded_file is not None:
    st.session_state.uploaded_file = uploaded_file
    df = pd.read_csv(uploaded_file)
    st.write("Uploaded CSV Preview", df.head())

    if st.button("Process and Generate Excel"):
        with st.spinner("Processing..."):
            st.session_state.output = process_csv_and_fetch_metadata(df)
        st.success("Processing complete! You can download the file below.")

if st.session_state.output is not None:
    filename = f"user_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    st.download_button("Download Excel", st.session_state.output, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if st.button("Reset"):
    st.session_state.uploaded_file = None
    st.session_state.output = None
    st.experimental_rerun()
