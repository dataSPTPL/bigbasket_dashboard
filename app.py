import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# Google Sheets connection
def get_google_sheets_data(spreadsheet_name="POLKA"):
    # Create credentials from secrets
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(credentials)
    
    sheet = client.open(spreadsheet_name).sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def main():
    st.title("BigBasket Stock Availability Dashboard")
    
    try:
        df = get_google_sheets_data()
        
        # Your original logic remains here
        brands = df['Brand'].unique()
        selected_brand = st.selectbox("Select a Brand", brands)
        
        # ... [Keep all your original code from def main()] ...

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

if __name__ == "__main__":
    main()