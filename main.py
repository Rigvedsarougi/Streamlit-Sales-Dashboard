import streamlit as st
from app import generate_sales_report as app_sales_report
from dash import generate_sales_report as dash_sales_report

st.set_page_config(page_title="Employee Sales App", layout="wide")

# Sidebar for page navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a Page", ["Page 1: Employee Sales Report", "Page 2: Sales Dashboard"])

# Load the appropriate page based on selection
if page == "Page 1: Employee Sales Report":
    st.title("Page 1: Employee Sales Report")
    app_sales_report()
elif page == "Page 2: Sales Dashboard":
    st.title("Page 2: Sales Dashboard")
    dash_sales_report()
