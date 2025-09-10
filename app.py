import streamlit as st
import pandas as pd
import requests
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime

# --- Function to fetch metadata for a single UID ---
def fetch_metadata(user_id):
    base_url = "https://sso.tpml.in/auth/get-user-metadata?userId="
    url = base_url + str(user_id)

    try:
        response = requests.get(url, timeout=10)  # add headers if needed
        if response.status_code == 200:
            data = response.json()
            metadata = data.get("metadata", {})
            return {
                "User ID": user_id,
                "Display Name": metadata.get("displayName", "N/A"),
                "First Name": metadata.get("first_name", "N/A"),
                "Last Name": metadata.get("last_name", "N/A"),
                "Email": metadata.get("dh", {}).get("newsLetter", {}).get("email", "N/A"),
                "Gender": metadata.get("gender", "N/A"),
                "DOB": f'{metadata.get("dob", {}).get("day", "N/A")}-'
                       f'{metadata.get("dob", {}).get("month", "N/A")}-'
                       f'{metadata.get("dob", {}).get("year", "N/A")}',
                "College": metadata.get("college", "N/A"),
            }
        else:
            return {"User ID": user_id, "Error": f"Failed ({response.status_code})"}
    except Exception as e:
        return {"User ID": user_id, "Error": str(e)}

# --- Streamlit UI ---
st.title("DECCAN HEARLD")

# Option 1: Enter a single UID
uid_input = st.text_input("Enter a UID to fetch Details:")

if st.button("Fetch Single UID") and uid_input:
    result = fetch_metadata(uid_input)
    st.json(result)

# Divider
st.markdown("---")

# Option 2: Upload a CSV
uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("📄 Uploaded CSV Preview", df.head())

    if st.button("Process CSV and Download Excel"):
        user_ids = df['UID'].unique().tolist()

        wb = Workbook()
        ws = wb.active
        ws.title = "User Metadata"
        headers = ["User ID", "Display Name", "First Name", "Last Name", "Email", "Gender", "DOB", "College"]
        ws.append(headers)

        results = []
        for uid in user_ids:
            meta = fetch_metadata(uid)
            results.append(meta)
            ws.append([meta.get(h, "") for h in headers])

        # Show results in Streamlit
        st.write("✅ Results", pd.DataFrame(results))

        # Save to Excel
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        filename = f"user_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        st.download_button(
            "⬇️ Download Excel",
            output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

