import streamlit as st
import pandas as pd
import requests
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime

def process_csv_and_fetch_metadata(input_df):
    """
    Processes the input DataFrame to fetch user metadata from the API
    and returns a downloadable Excel file in a BytesIO object.
    """
    # Ensure the 'UID' column exists
    if 'UID' not in input_df.columns:
        st.error("The uploaded CSV must contain a column named 'UID'.")
        return None

    user_ids = input_df['UID'].unique().tolist()
    wb = Workbook()
    ws = wb.active
    ws.title = "User Metadata"

    # Define headers for the Excel file
    headers = ["User ID", "Display Name", "First Name", "Last Name", "Email", "Gender", "DOB", "College", "API Status", "Error Details"]
    ws.append(headers)

    base_url = "https://sso-dev.tpml.in/auth/get-user-metadata?userId="

    # Initialize a progress bar for user feedback
    progress_bar = st.progress(0)
    total_users = len(user_ids)
    
    st.info("Starting to process and fetch user metadata...")

    for i, user_id in enumerate(user_ids):
        try:
            url = base_url + str(user_id)
            response = requests.get(url, timeout=10) # Added a timeout for robustness

            if response.status_code == 200:
                data = response.json()
                metadata = data.get("metadata", {})
                
                # Check if 'metadata' key is present and is not empty
                if metadata:
                    display_name = metadata.get("displayName", "N/A")
                    first_name = metadata.get("first_name", "N/A")
                    last_name = metadata.get("lastName", "N/A")
                    
                    # Safely access nested dictionary
                    email = metadata.get("dh", {}).get("newsLetter", {}).get("email", "N/A")
                        
                    gender = metadata.get("gender", "N/A")
                    
                    # Safely handle DOB dictionary
                    dob_parts = metadata.get("dob", {})
                    dob = f'{dob_parts.get("day", "N/A")}-{dob_parts.get("month", "N/A")}-{dob_parts.get("year", "N/A")}'
                    
                    college = metadata.get("college", "N/A")
                    
                    row = [user_id, display_name, first_name, last_name, email, gender, dob, college, "Success", ""]
                    ws.append(row)
                else:
                    # Case for 200 OK but no metadata in the response
                    row = [user_id, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "Success (No Metadata)", "API returned 200 OK but 'metadata' key is empty or missing."]
                    ws.append(row)
            else:
                # Case for non-200 status codes
                error_detail = f"API returned non-200 status code: {response.status_code}. Response: {response.text}"
                row = [user_id, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", f"Failed ({response.status_code})", error_detail]
                ws.append(row)
        
        except requests.exceptions.RequestException as e:
            # Handle network-related errors (e.g., timeout, connection error)
            error_detail = f"Network or API request error: {e}"
            row = [user_id, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "Failed (Request Exception)", error_detail]
            ws.append(row)
        except Exception as e:
            # Catch any other unexpected errors
            error_detail = f"An unexpected error occurred: {e}"
            row = [user_id, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "Failed (General Error)", error_detail]
            ws.append(row)

        progress_bar.progress((i + 1) / total_users)

    # Save to BytesIO for in-memory download
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

# --- Streamlit UI ---
st.set_page_config(page_title="User Metadata Fetcher", layout="wide")
st.title("User Metadata Fetcher")

# Initialize session state variables
if 'process_complete' not in st.session_state:
    st.session_state.process_complete = False
if 'output_data' not in st.session_state:
    st.session_state.output_data = None
if 'processed_filename' not in st.session_state:
    st.session_state.processed_filename = ""

uploaded_file = st.file_uploader("Upload CSV with UID column", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("Uploaded CSV Preview")
    st.dataframe(df.head())
    
    if st.button("Start Processing"):
        with st.spinner("Processing... Please wait."):
            st.session_state.output_data = process_csv_and_fetch_metadata(df)
            if st.session_state.output_data:
                st.session_state.process_complete = True
                # Store the dynamically generated filename in session state
                st.session_state.processed_filename = f"user_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        if st.session_state.process_complete:
            st.success("Processing complete! Your file is ready for download.")

# Display the download button only after processing is complete
if st.session_state.process_complete and st.session_state.output_data:
    st.download_button(
        label="Download Excel File",
        data=st.session_state.output_data,
        file_name=st.session_state.processed_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    # Optional button to reset the app for a new file
    if st.button("Start New Process"):
        st.session_state.process_complete = False
        st.session_state.output_data = None
        st.experimental_rerun()
