import streamlit as st
import pandas as pd
import plotly.express as px

# Load Data with updated cache method
@st.cache_data
def load_data():
    df = pd.read_csv('All - All.csv')
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y', errors='coerce')
    df['Year-Month'] = df['Order Date'].dt.to_period('M').astype(str)
    return df

# Generate Sales Report with detailed checks
def generate_sales_report(df, employee_name):
    filtered_df = df[df['Employee Name'] == employee_name]
    
    if filtered_df.empty:
        st.write(f"No data found for employee: {employee_name}")
        return None, None
    
    # Step 1: Check the filtered dataframe
    st.write("Filtered DataFrame (Sample):", filtered_df.head())

    # Step 2: Group to get first order date
    first_order_date = filtered_df.groupby('Shop Name')['Order Date'].min().reset_index()
    first_order_date.rename(columns={'Order Date': 'First Order Date'}, inplace=True)  # Renaming for clarity

    # Step 3: Check the first_order_date dataframe
    st.write("First Order Date DataFrame (Sample):", first_order_date.head())

    # Step 4: Perform the merge
    merged_df = pd.merge(filtered_df, first_order_date, on='Shop Name', how='left')

    # Step 5: Check the merged_df
    st.write("Merged DataFrame (Columns):", merged_df.columns)
    st.write("Merged DataFrame (Sample):", merged_df.head())

    if 'First Order Date' not in merged_df.columns:
        st.write("Error: 'First Order Date' column not found after merge.")
        return None, None
    
    # Identifying new shops
    new_shops = merged_df[merged_df['Order Date'] == merged_df['First Order Date']]
    
    # Dropping duplicates to identify unique orders
    unique_orders = filtered_df.drop_duplicates(subset=['Shop Name', 'Order Date'])
    
    # Orders after the first order for repeated shops
    unique_orders_after_first = unique_orders[unique_orders['Year-Month'] > unique_orders['Shop Name'].map(
        first_order_date.set_index('Shop Name')['First Order Date'].dt.to_period('M'))]

    # Creating the monthly report
    report = filtered_df.groupby('Year-Month').agg(
        total_shops=('Shop Name', 'nunique'),
        total_sales=('Order Value', 'sum')
    ).reset_index()

    repeated_shops_per_month = unique_orders_after_first.groupby('Year-Month')['Shop Name'].nunique().reset_index(name='repeated_shops')
    new_shops_per_month = new_shops.groupby('Year-Month')['Shop Name'].nunique().reset_index(name='new_shops')

    repeated_shop_order_value = unique_orders_after_first.groupby('Year-Month')['Order Value'].sum().reset_index(name='repeated_order_value')
    new_shop_order_value = new_shops.groupby('Year-Month')['Order Value'].sum().reset_index(name='new_order_value')

    # Merging all reports together
    final_report = pd.merge(report, repeated_shops_per_month, on='Year-Month', how='left')
    final_report = pd.merge(final_report, new_shops_per_month, on='Year-Month', how='left')
    final_report = pd.merge(final_report, repeated_shop_order_value, on='Year-Month', how='left')
    final_report = pd.merge(final_report, new_shop_order_value, on='Year-Month', how='left')

    final_report.fillna(0, inplace=True)
    
    return final_report, filtered_df

# Streamlit App
st.title("Employee Sales Dashboard")

# Load Data
df = load_data()

# Employee Dropdown
employee_names = df['Employee Name'].unique()
selected_employee = st.selectbox('Select an Employee:', employee_names)

# Generate Report Button
if st.button('Generate Report'):
    final_report, filtered_df = generate_sales_report(df, selected_employee)
    
    if final_report is not None:
        st.write("Final Report (Sample):", final_report.head())
