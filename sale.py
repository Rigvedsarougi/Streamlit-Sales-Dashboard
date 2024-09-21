import streamlit as st
import pandas as pd
import plotly.express as px

# Load the data
biolume_df = pd.read_csv('All - All.csv')
biolume_df['Order Date'] = pd.to_datetime(biolume_df['Order Date'], format='%d-%m-%Y', errors='coerce')

# Function to generate the sales report
def generate_sales_report(employee_name):
    # Filter data by Employee Name
    filtered_df = biolume_df[biolume_df['Employee Name'] == employee_name]

    if filtered_df.empty:
        st.write(f"No data found for employee: {employee_name}")
        return

    filtered_df['Year-Month'] = filtered_df['Order Date'].dt.to_period('M').astype(str)

    # Identify new and repeated shops
    first_order_date = filtered_df.groupby('Shop Name')['Order Date'].min().reset_index()
    merged_df = pd.merge(filtered_df, first_order_date, on='Shop Name', suffixes=('', '_first'))

    new_shops = merged_df[merged_df['Order Date'] == merged_df['Order Date_first']]
    unique_orders = filtered_df.drop_duplicates(subset=['Shop Name', 'Order Date'])
    unique_orders_after_first = unique_orders[unique_orders['Year-Month'] > unique_orders['Shop Name'].map(first_order_date.set_index('Shop Name')['Order Date'].dt.to_period('M'))]

    # Generate summary statistics
    report = filtered_df.groupby('Year-Month').agg(
        total_shops=('Shop Name', 'nunique'),
        total_sales=('Order Value', 'sum'),
    ).reset_index()

    repeated_shops_per_month = unique_orders_after_first.groupby('Year-Month')['Shop Name'].nunique().reset_index(name='repeated_shops')
    new_shops_per_month = new_shops.groupby('Year-Month')['Shop Name'].nunique().reset_index(name='new_shops')

    repeated_shop_order_value = unique_orders_after_first.groupby('Year-Month')['Order Value'].sum().reset_index(name='repeated_order_value')
    new_shop_order_value = new_shops.groupby('Year-Month')['Order Value'].sum().reset_index(name='new_order_value')

    # Merge reports
    final_report = pd.merge(report, repeated_shops_per_month, on='Year-Month', how='left')
    final_report = pd.merge(final_report, new_shops_per_month, on='Year-Month', how='left')
    final_report = pd.merge(final_report, repeated_shop_order_value, on='Year-Month', how='left')
    final_report = pd.merge(final_report, new_shop_order_value, on='Year-Month', how='left')
    final_report.fillna(0, inplace=True)

    # Calculate additional metrics
    avg_monthly_sales = final_report['total_sales'].mean()
    total_repeated_order_value = final_report['repeated_order_value'].sum()
    avg_repeated_order_value = final_report['repeated_order_value'].mean()
    total_new_order_value = final_report['new_order_value'].sum()
    avg_new_order_value = final_report['new_order_value'].mean()

    # Layout for the dashboard
    st.write(f"### Sales Report for Employee: {employee_name}")
    
    # KPI Metrics
    st.markdown("<h4 style='font-size: 18px;'>Key Performance Indicators</h4>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    metric_style = "<p style='font-size: 14px;'>%s</p>"
    col1.markdown(metric_style % f"Total Sales: {final_report['total_sales'].sum():,.2f}", unsafe_allow_html=True)
    col2.markdown(metric_style % f"Avg Monthly Sales: {avg_monthly_sales:,.2f}", unsafe_allow_html=True)
    col3.markdown(metric_style % f"Total Repeated Order Value: {total_repeated_order_value:,.2f}", unsafe_allow_html=True)
    col4.markdown(metric_style % f"Avg Repeated Order Value: {avg_repeated_order_value:,.2f}", unsafe_allow_html=True)
    col5.markdown(metric_style % f"Total New Order Value: {total_new_order_value:,.2f}", unsafe_allow_html=True)
    col6.markdown(metric_style % f"Avg New Order Value: {avg_new_order_value:,.2f}", unsafe_allow_html=True)

    # Sales Chart
    st.markdown("#### Monthly Total Sales")
    fig = px.bar(final_report, x='Year-Month', y='total_sales', title="Total Sales Per Month",
                 labels={'total_sales': 'Total Sales', 'Year-Month': 'Year-Month'})
    st.plotly_chart(fig, use_container_width=True)

    # Repeated and New Order Chart
    st.markdown("#### Monthly Repeated and New Shop Order Values")
    fig2 = px.bar(final_report, x='Year-Month', y=['repeated_order_value', 'new_order_value'],
                  title="Repeated and New Shop Order Values", 
                  labels={'value': 'Order Value', 'Year-Month': 'Year-Month'},
                  barmode='group')
    st.plotly_chart(fig2, use_container_width=True)

    # New Shops and Repeated Shops Table
    st.markdown("#### Month-wise New and Repeated Shop Names with Order Values")
    new_shops_grouped = new_shops.groupby(['Year-Month', 'Shop Name']).agg(total_order_value=('Order Value', 'sum')).reset_index()
    repeated_shops_grouped = unique_orders_after_first.groupby(['Year-Month', 'Shop Name']).agg(total_order_value=('Order Value', 'sum')).reset_index()
    st.markdown("**New Shops and Their Total Order Values**")
    st.dataframe(new_shops_grouped)
    st.markdown("**Repeated Shops and Their Total Order Values**")
    st.dataframe(repeated_shops_grouped)

# Streamlit App UI
st.title("Employee Sales Dashboard")
employee_names = biolume_df['Employee Name'].unique()
selected_employee = st.selectbox('Select an Employee:', employee_names)
if st.button('Generate Report'):
    generate_sales_report(selected_employee)
