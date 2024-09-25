import streamlit as st
import pandas as pd

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

    # Extract the year-month for easier grouping
    filtered_df['Year-Month'] = filtered_df['Order Date'].dt.to_period('M')

    # Find the first order date (month) for each shop
    first_order_date = filtered_df.groupby('Shop Name')['Order Date'].min().reset_index()

    # Merge the first order date back with the original dataframe
    merged_df = pd.merge(filtered_df, first_order_date, on='Shop Name', suffixes=('', '_first'))

    # Identify new shops: where the order date matches their first order date
    new_shops = merged_df[merged_df['Order Date'] == merged_df['Order Date_first']]

    # Identify repeated shops: where the order date is later than their first order date
    repeated_shops = merged_df[merged_df['Order Date'] > merged_df['Order Date_first']]

    # Generate the report for total, repeated, and new shops
    report = filtered_df.groupby('Year-Month').agg(
        total_shops=('Shop Name', 'nunique'),  # Total unique shops where sales happened
        total_sales=('Order Value', 'sum'),    # Total sales for the month
    ).reset_index()

    # Count the number of repeated shops per month
    repeated_shops_per_month = repeated_shops.groupby('Year-Month')['Shop Name'].nunique().reset_index(name='repeated_shops')

    # Count the number of new shops per month
    new_shops_per_month = new_shops.groupby('Year-Month')['Shop Name'].nunique().reset_index(name='new_shops')

    # Calculate the order value for repeated and new shops
    repeated_shop_order_value = repeated_shops.groupby('Year-Month')['Order Value'].sum().reset_index(name='repeated_order_value')
    new_shop_order_value = new_shops.groupby('Year-Month')['Order Value'].sum().reset_index(name='new_order_value')

    # Merge all results into a single report
    final_report = pd.merge(report, repeated_shops_per_month, on='Year-Month', how='left')
    final_report = pd.merge(final_report, new_shops_per_month, on='Year-Month', how='left')
    final_report = pd.merge(final_report, repeated_shop_order_value, on='Year-Month', how='left')
    final_report = pd.merge(final_report, new_shop_order_value, on='Year-Month', how='left')

    # Fill NaN values with 0 (for months where no new or repeated shops exist)
    final_report.fillna(0, inplace=True)

    # Calculate average monthly sales
    avg_monthly_sales = final_report['total_sales'].mean()

    # Calculate total and average monthly order value for repeated and new shops
    total_repeated_order_value = final_report['repeated_order_value'].sum()
    avg_repeated_order_value = final_report['repeated_order_value'].mean()

    total_new_order_value = final_report['new_order_value'].sum()
    avg_new_order_value = final_report['new_order_value'].mean()

    # 1st Table: Monthly Sales, Total Sales, and Order Values for Repeated and New Shops
    st.write(f"Sales Report for Employee: {employee_name}")
    st.write("**Monthly Sales of Every Month, Average Monthly Sale, Total Sales of Total Shops, Repeated Shops, New Shops, and Order Values**")
    st.table(final_report[['Year-Month', 'total_shops', 'total_sales', 'repeated_shops', 'new_shops', 'repeated_order_value', 'new_order_value']])
    
    # Display total and average values
    st.write(f"Average Monthly Sales: {avg_monthly_sales:.2f}")
    st.write(f"Total Sales: {final_report['total_sales'].sum():.2f}")
    st.write(f"Total Repeated Order Value: {total_repeated_order_value:.2f}")
    st.write(f"Average Repeated Order Value: {avg_repeated_order_value:.2f}")
    st.write(f"Total New Order Value: {total_new_order_value:.2f}")
    st.write(f"Average New Order Value: {avg_new_order_value:.2f}")

    # 2nd Table: Month-wise New and Repeated Shop Names with Total Order Values

    # Get new shop names and their total order values per month
    new_shops_grouped = new_shops.groupby(['Year-Month', 'Shop Name']).agg(
        total_order_value=('Order Value', 'sum')
    ).reset_index()

    # Get repeated shop names and their total order values per month
    repeated_shops_grouped = repeated_shops.groupby(['Year-Month', 'Shop Name']).agg(
        total_order_value=('Order Value', 'sum')
    ).reset_index()

    # Display new and repeated shop names with their total order values
    st.write("**New Shops and Their Total Order Values**")
    st.table(new_shops_grouped)

    st.write("**Repeated Shops and Their Total Order Values**")
    st.table(repeated_shops_grouped)

# Streamlit App UI
st.title("Employee Sales Report")

# Dropdown for employee selection
employee_names = biolume_df['Employee Name'].unique()
selected_employee = st.selectbox('Select an Employee:', employee_names)

# Button to generate the report
if st.button('Generate Report'):
    generate_sales_report(selected_employee)
