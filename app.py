def process_csv_and_fetch_metadata(input_df):
    user_ids = input_df['UID'].unique().tolist()
    wb = Workbook()
    ws = wb.active
    ws.title = "User Metadata"

    headers_row = ["User ID", "Display Name", "First Name", "Last Name", "Email", "Gender", "DOB", "College"]
    ws.append(headers_row)

    base_url = "https://sso.tpml.in/auth/get-user-metadata?userId="
    headers = {
        "Authorization": "Bearer YOUR_TOKEN_HERE",  # add if required
        "Content-Type": "application/json"
    }

    for user_id in user_ids:
        url = base_url + str(user_id)
        response = requests.get(url, headers=headers)

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
            row = [user_id, f"Failed: {response.status_code}", "", "", "", "", "", ""]
            ws.append(row)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

