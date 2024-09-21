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

# Generate Sales Report with column existence check
def generate_sales_report(df, employee_name):
    filtered_df = df[df['Employee Name'] == employee_name]
    
    if filtered_df.empty:
        st.write(f"No data found for employee: {employee_name}")
        return None, None
    
    # Fixing the column renaming issue during the merge
    first_order_date = filtered_df.groupby('Shop Name')['Order Date'].min().reset_index()
    first_order_date.rename(columns={'Order Date': 'First Order Date'}, inplace=True)  # Renaming for clarity
    
    merged_df = pd.merge(filtered_df, first_order_date, on='Shop Name', how='left')

    # Debugging - check if the merge happened correctly
    st.write("Merged DataFrame Columns:", merged_df.columns)
    
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

# Display KPIs
def display_kpis(final_report):
    st.markdown("<h4 style='font-size: 18px;'>Key Performance Indicators</h4>", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    col1.metric("Total Sales", f"{final_report['total_sales'].sum():,.2f}")
    col2.metric("Avg Monthly Sales", f"{final_report['total_sales'].mean():,.2f}")
    col3.metric("Total Repeated Order Value", f"{final_report['repeated_order_value'].sum():,.2f}")
    col4.metric("Avg Repeated Order Value", f"{final_report['repeated_order_value'].mean():,.2f}")
    col5.metric("Total New Order Value", f"{final_report['new_order_value'].sum():,.2f}")
    col6.metric("Avg New Order Value", f"{final_report['new_order_value'].mean():,.2f}")

# Display Charts
def display_charts(final_report):
    st.markdown("#### Monthly Total Sales")
    fig1 = px.bar(final_report, x='Year-Month', y='total_sales', title="Total Sales Per Month")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("#### Monthly Repeated and New Shop Order Values")
    fig2 = px.bar(final_report, x='Year-Month', y=['repeated_order_value', 'new_order_value'],
                  title="Repeated and New Shop Order Values", barmode='group')
    st.plotly_chart(fig2, use_container_width=True)

# Display Tables
def display_tables(final_report, filtered_df):
    # New Shops Grouped Table
    new_shops_grouped = filtered_df[filtered_df['Order Date'] == filtered_df['First Order Date']].groupby(
        ['Year-Month', 'Shop Name']).agg(total_order_value=('Order Value', 'sum')).reset_index()

    # Repeated Shops Grouped Table
    repeated_shops_grouped = filtered_df.groupby(['Year-Month', 'Shop Name']).agg(
        total_order_value=('Order Value', 'sum')).reset_index()

    st.markdown("**New Shops and Their Total Order Values**")
    st.dataframe(new_shops_grouped)
    
    st.markdown("**Repeated Shops and Their Total Order Values**")
    st.dataframe(repeated_shops_grouped)

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
        display_kpis(final_report)
        display_charts(final_report)
        display_tables(final_report, filtered_df)
