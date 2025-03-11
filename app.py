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
    
    # Initialize session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'selected_brand' not in st.session_state:
        st.session_state.selected_brand = None
    
    # Add a button to trigger analysis
    if st.button("Load Data and Analyze"):
        try:
            # Status: Loading data
            with st.status("Loading data from Google Sheets...", expanded=True) as status:
                df = get_google_sheets_data()
                st.session_state.df = df  # Save data to session state
                st.session_state.data_loaded = True
                st.write("✅ Data loaded successfully!")
                status.update(label="Data loaded!", state="complete", expanded=False)
            
            # Debug: Show raw data
            with st.expander("🔍 Raw Data Preview"):
                st.dataframe(st.session_state.df.head(3))
                st.write("Columns in Data:", st.session_state.df.columns.tolist())
            
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            st.write("Debug Info:")
            st.write(f"Exception Type: {type(e).__name__}")
            st.write(f"Exception Details: {str(e)}")
    
    # Proceed only if data is loaded
    if st.session_state.data_loaded:
        df = st.session_state.df
        
        # Check if required columns exist
        required_columns = ['Brand', 'Product', 'Stock Availability', 'Discounted Price', 'Pack']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"❌ Missing columns in data: {missing_columns}")
            return
        
        # Get unique brands
        brands = df['Brand'].unique()
        
        # Brand selection
        selected_brand = st.selectbox("Select a Brand", brands, key="brand_select")
        st.session_state.selected_brand = selected_brand
        st.success(f"✅ Selected Brand: **{selected_brand}**")
        
        # Filter data for selected brand
        with st.spinner(f"Filtering data for {selected_brand}..."):
            brand_data = df[df['Brand'] == selected_brand]
            st.write(f"📊 Found **{len(brand_data)}** products for **{selected_brand}**")
        
        # Stock analysis
        st.subheader(f"📈 Stock Analysis for {selected_brand}")
        
        # Count products
        with st.spinner("Calculating stock metrics..."):
            total_products = len(brand_data)
            in_stock = len(brand_data[brand_data['Stock Availability'] == 'N/A'])
            out_of_stock = len(brand_data[brand_data['Stock Availability'] == 'Currently unavailable'])
        
        # Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Products", total_products)
            st.metric("In Stock", in_stock)
        with col2:
            st.metric("Out of Stock", out_of_stock)
        
        # List out-of-stock products
        if out_of_stock > 0:
            st.subheader("❌ Out of Stock Products")
            out_of_stock_products = brand_data[brand_data['Stock Availability'] == 'Currently unavailable']
            st.table(out_of_stock_products[['Product', 'Pack', 'Discounted Price']])
        else:
            st.success("✅ All products are currently in stock!")
            
        # Show all products
        st.subheader("📦 All Products")
        st.dataframe(brand_data[['Product', 'Stock Availability', 'Discounted Price', 'Pack']])

if __name__ == "__main__":
    main()