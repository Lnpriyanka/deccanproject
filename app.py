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
    ws.title = "User Metadata"

    headers = ["User ID", "Display Name", "First Name", "Last Name", "Email", "Gender", "DOB", "College"]
    ws.append(headers)

    base_url = "https://sso-dev.tpml.in/auth/get-user-metadata?userId="

    progress_bar = st.progress(0)
    total_users = len(user_ids)

    for i, user_id in enumerate(user_ids):
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

        progress_bar.progress((i + 1) / total_users)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

st.set_page_config(page_title="User Metadata Fetcher", layout="wide")
st.title("User Metadata Fetcher")
st.write("Upload a CSV file with a column named 'UID' to fetch user metadata from the API.")

if 'process_complete' not in st.session_state:
    st.session_state.process_complete = False
if 'output_data' not in st.session_state:
    st.session_state.output_data = None

uploaded_file = st.file_uploader("Upload CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("CSV Data Preview")
    st.dataframe(df.head())

    if st.button("Start Processing"):
        with st.spinner("Processing... Please wait."):
            st.session_state.output_data = process_csv_and_fetch_metadata(df)
            st.session_state.process_complete = True
        st.success("Processing complete!")

if st.session_state.process_complete and st.session_state.output_data:
    filename = f"user_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    st.download_button(
        "Download Processed Excel File",
        st.session_state.output_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    if st.button("Start New Process"):
        st.session_state.process_complete = False
        st.session_state.output_data = None
        st.experimental_rerun()
