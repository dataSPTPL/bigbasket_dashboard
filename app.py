import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# Google Sheets connection
def get_google_sheets_data(spreadsheet_name="POLKA"):
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

# Email notification function
def send_stockout_email(brand, email, out_of_stock_products):
    sender_email = st.secrets["email"]["sender"]
    sender_password = st.secrets["email"]["password"]
    
    subject = f"Stock Alert: {brand} - Products Out of Stock"
    body = f"""
    Dear {brand} Team,
    
    The following products are currently out of stock as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:
    
    {out_of_stock_products[['Product', 'Pack', 'Discounted Price']].to_string(index=False)}
    
    Please take necessary action to restock these items.
    
    Regards,
    BigBasket Stock Monitoring System
    """
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = email
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email to {email}: {str(e)}")
        return False

def main():
    # Set page config
    st.set_page_config(
        page_title="BigBasket Stock Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"  # Sidebar hidden initially
    )

    # Professional Helium10-inspired CSS
    st.markdown("""
    <style>
    .main {background-color: #1a1a1a; color: #ffffff;}
    h1, h2, h3, h4 {color: #00d4b4;}
    .stButton>button {
        background-color: #00d4b4;
        color: #ffffff;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #00b394;
    }
    .metric-card {
        background-color: #2d2d2d;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin: 10px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #2d2d2d;
        border-bottom: 2px solid #00d4b4;
    }
    .stTabs [data-baseweb="tab"] {
        color: #ffffff;
        padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #3d3d3d;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 2px solid #00d4b4;
        color: #00d4b4;
    }
    .stDataFrame {background-color: #2d2d2d; color: #ffffff;}
    .center-form {max-width: 500px; margin: 50px auto; padding: 20px; background-color: #2d2d2d; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 BigBasket Stock Dashboard")
    st.markdown('<span style="color: #b0b0b0;">Real-time stock monitoring and analytics</span>', unsafe_allow_html=True)

    # Initialize session state
    if 'data_loaded' not in st.session_state:
        with st.spinner("Loading data from Google Sheets..."):
            df = get_google_sheets_data()
            st.session_state.df = df
            st.session_state.data_loaded = True
    if 'brand_emails' not in st.session_state:
        st.session_state.brand_emails = {}
    if 'email_sent' not in st.session_state:
        st.session_state.email_sent = {}
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False

    # Center form for brand entry on initial load
    if not st.session_state.show_results:
        with st.container():
            st.markdown('<div class="center-form">', unsafe_allow_html=True)
            st.subheader("Add Brands to Monitor")
            with st.form("brand_config"):
                brand_name = st.text_input("Brand Name")
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.form_submit_button("Add Brand"):
                        if brand_name and brand_name not in st.session_state.brand_emails:
                            st.session_state.brand_emails[brand_name] = None  # No email yet
                            st.success(f"Added {brand_name}")
                        elif brand_name in st.session_state.brand_emails:
                            st.warning(f"{brand_name} already added!")
                        else:
                            st.error("Please enter a brand name.")
                with col2:
                    if st.form_submit_button("Load Results"):
                        if st.session_state.brand_emails:
                            st.session_state.show_results = True
                        else:
                            st.error("Add at least one brand to load results!")
            st.markdown('</div>', unsafe_allow_html=True)

    # Show results after loading
    if st.session_state.show_results and st.session_state.data_loaded:
        df = st.session_state.df
        
        # Verify required columns
        required_columns = ['Brand', 'Product', 'Stock Availability', 'Discounted Price', 'Pack']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Missing columns in data: {missing_columns}")
            return

        # Display configured brands with email option
        st.subheader("Configured Brands")
        for brand in list(st.session_state.brand_emails.keys()):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"- {brand}")
            with col2:
                if st.session_state.brand_emails[brand] is None:
                    with st.form(f"email_form_{brand}", clear_on_submit=True):
                        email = st.text_input(f"Email for {brand}", key=f"email_{brand}")
                        if st.form_submit_button("Add Email"):
                            if email:
                                st.session_state.brand_emails[brand] = email
                                st.success(f"Email added for {brand}")
                            else:
                                st.error("Please enter an email.")
                else:
                    st.write(f"Email: {st.session_state.brand_emails[brand]}")

        # Multi-brand selection from configured brands
        selected_brands = st.multiselect(
            "Select Brands to Monitor (up to 10)",
            options=list(st.session_state.brand_emails.keys()),
            default=list(st.session_state.brand_emails.keys())[:1],
            max_selections=10
        )

        if selected_brands:
            brand_data = df[df['Brand'].isin(selected_brands)]
            
            # Tabs for different views
            tab1, tab2, tab3 = st.tabs(["📈 Overview", "❌ Out of Stock", "📦 All Products"])
            
            with tab1:
                st.subheader("Stock Overview")
                for brand in selected_brands:
                    brand_df = brand_data[brand_data['Brand'] == brand]
                    total = len(brand_df)
                    in_stock = len(brand_df[brand_df['Stock Availability'] == 'N/A'])
                    out_of_stock = len(brand_df[brand_df['Stock Availability'] == 'Currently unavailable'])
                    
                    st.markdown(f"### {brand}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("Total Products", total, delta_color="off")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("In Stock", in_stock, delta_color="off")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col3:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("Out of Stock", out_of_stock, delta_color="off")
                        st.markdown('</div>', unsafe_allow_html=True)

            with tab2:
                st.subheader("Out of Stock Products")
                for brand in selected_brands:
                    brand_df = brand_data[brand_data['Brand'] == brand]
                    out_of_stock_df = brand_df[brand_df['Stock Availability'] == 'Currently unavailable']
                    if not out_of_stock_df.empty:
                        st.markdown(f"#### {brand}")
                        st.table(out_of_stock_df[['Product', 'Pack', 'Discounted Price']])
                        if st.session_state.brand_emails[brand] and (brand not in st.session_state.email_sent or not st.session_state.email_sent[brand]):
                            if send_stockout_email(brand, st.session_state.brand_emails[brand], out_of_stock_df):
                                st.success(f"Auto-sent stock alert to {st.session_state.brand_emails[brand]}")
                                st.session_state.email_sent[brand] = True
                    else:
                        st.success(f"All {brand} products are in stock!")

            with tab3:
                st.subheader("All Products")
                st.dataframe(brand_data[['Brand', 'Product', 'Stock Availability', 'Discounted Price', 'Pack']])

if __name__ == "__main__":
    main()