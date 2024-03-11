# import required libraries
import streamlit as st
import pandas as pd
import seaborn as sns
import plotly.express as px

# read dataset
alldata = pd.read_csv('alldata.csv')

# CODE
# convert object to datetime
to_datetime = alldata.loc[:, ('order_purchase_timestamp',
                             'order_approved_at',
                             'order_delivered_carrier_date', 'order_delivered_customer_date',
                             'order_estimated_delivery_date')]

for col in to_datetime:
    alldata[col] = pd.to_datetime(alldata[col], format='%Y-%m-%d %H:%M:%S', errors='coerce')

# filter dataset to period of analysis: 2017-02 until 2018-08
df_filtered = alldata[(alldata['order_purchase_timestamp'] >= "2017-02-01 00:00:00") & (alldata['order_purchase_timestamp'] < "2018-09-01 00:00:00")]

# SHOW
backgroundColor = "#F0F0F0"

st.header('E-commerce Dashboard', divider='rainbow')

# add columns for KPI
col1, col2, col3 = st.columns(3)

with col1:
    total_customers = df_filtered.customer_unique_id.nunique()
    st.metric('Total customers', value=total_customers)

with col2:
    total_orders = df_filtered.order_id.nunique()
    st.metric('Total orders', value=total_orders)

with col3:
    mon = str(df_filtered.payment_value.sum().round()) + ' R$'
    st.metric('Total monetary value', value=mon)

# CODE
# add element: monthly monetary growth, monthly total customers, and monthly total orders
# grouping dataset then renaming it
monthly_agg = df_filtered.groupby(df_filtered['order_purchase_timestamp'].dt.to_period('M')).agg({
        'payment_value': 'sum',
        'order_id': 'nunique',
        'customer_unique_id': 'nunique'
    }).reset_index()

monthly_agg = monthly_agg.rename(columns={
    'order_purchase_timestamp': 'month',
    'payment_value': 'total_payment_value',
    'order_id': 'unique_order_count',
    'customer_unique_id': 'unique_customer_count'
})

# convert 'month' to a string representation
monthly_agg['month'] = monthly_agg['month'].dt.strftime('%Y-%m')

# using pct_change() function to see monthly percentage change
monthly_agg['monthly_payment_value_growth'] = monthly_agg['total_payment_value'].pct_change()

# SHOW
# add column selection
line_var_default = "monthly_payment_value_growth"

if st.sidebar.button("monthly_payment_value_growth"):
    line_var_default_var = "monthly_payment_value_growth"
if st.sidebar.button("unique_customer_count"):
    line_var_default_var = "unique_customer_count"
if st.sidebar.button("unique_order_count"):
    line_var_default_var = "unique_order_count"

options_line = monthly_agg[['monthly_payment_value_growth', 'unique_customer_count', 'unique_order_count']].columns
line_selection = st.selectbox("Choose a variable:", options_line)

# visualize the line plot
st.subheader(f"{line_selection}")
fig = px.line(monthly_agg, x='month', y=line_selection)
fig.update_xaxes(title='Month')
fig.update_yaxes(title=f'{line_selection}')
st.plotly_chart(fig, theme='streamlit', use_container_width=True)

# CODE
# add element: RFM table
def create_rfm_df(df_filtered):
    rfm_df = df_filtered.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": 'max',
        "order_id": 'nunique',
        'payment_value': 'sum'
    })

    rfm_df.columns = ['customer_id', 'max_order_timestamp', 'frequency', 'monetary_value']

    rfm_df['max_order_timestamp'] = rfm_df['max_order_timestamp'].dt.date
    recent_date = df_filtered['order_purchase_timestamp'].dt.date.max()
    rfm_df['recency'] = rfm_df['max_order_timestamp'].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1)

    # segment customers using quartiles
    r_quartiles = pd.qcut(rfm_df['recency'], q=4, labels=range(4,0,-1))
    f_quartiles = pd.qcut(rfm_df['frequency'].rank(method='first'), q=4, labels=range(1,5), duplicates='drop')
    m_quartiles = pd.qcut(rfm_df['monetary_value'].rank(method='first'), q=4, labels=range(1,5), duplicates='drop')

    # building RFM segments: R | F | M
    rfm_df = rfm_df.assign(R=r_quartiles,F=f_quartiles,M=m_quartiles)

    # building RFM score: | R + F + M |
    rfm_df['RFM_segment'] = rfm_df['R'].astype(str) +\
                      rfm_df['F'].astype(str) +\
                      rfm_df['M'].astype(str)

    rfm_df['RFM_score'] = rfm_df[['R','F','M']].sum(axis=1)

    return rfm_df

# create rfm_df with columns: customer_id | recency | frequency | monetary_value | R | F | M | RFM_segment | RFM_score
rfm_df = create_rfm_df(df_filtered)

def customer_segments(RFM_segment):
    if RFM_segment == 444:
        return 'VIP'
    elif RFM_segment >= 433 and RFM_segment < 444:
        return 'Very Loyal'
    elif RFM_segment >= 421 and RFM_segment < 433:
        return 'Potential Loyalist'
    elif RFM_segment >= 344 and RFM_segment < 421:
        return 'New Customers'
    elif RFM_segment >=323 and RFM_segment < 344:
        return 'Potential Customers'
    elif RFM_segment >= 224 and RFM_segment < 323:
        return 'High risk to churn'
    else:
        return 'Lost Customers'

# convert 'RFM_segment' to int
rfm_df['RFM_segment'] = rfm_df['RFM_segment'].astype(int)

# defining RFM segment category
rfm_df['Segment'] = rfm_df['RFM_segment'].apply(customer_segments)

# summarize RFM mean in each defined segments
rfm_copy = rfm_df.reset_index().copy()
rfm_summary = rfm_copy.groupby('Segment').agg({
    'customer_id': 'count',
    'recency': 'mean',
    'frequency': 'mean',
    'monetary_value': 'mean',
}).round(3)

rfm_summary.rename(columns={
    'customer_id': 'Total customer',
    'recency': 'Avg. Recency',
    'frequency': 'Avg. Frequency',
    'monetary_value': 'Avg. Monetary'
}, inplace=True)

rfm_summary = rfm_summary.reset_index()

# add columns for RFM KPI
col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(),3)
    st.metric('Avg. Recency', value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(),3)
    st.metric('Avg. Frequency', value=avg_frequency)

with col3:
    avg_monetary = round(rfm_df.monetary_value.mean(),3)
    st.metric('Avg. Monetary value', value=avg_monetary)

# create new df to easier making plot
rfm_grouped = rfm_copy.groupby('Segment')['customer_id'].count().reset_index().sort_values(ascending=True, by='customer_id')

# SHOW
# draw the bar plot
st.subheader('Customer segmentation')
fig = px.bar(rfm_grouped, x='customer_id', y='Segment')
st.plotly_chart(fig, theme='streamlit', use_container_width=True)

# visualize the recency and monetary mean in each defined segments
col1, col2 = st.columns([2, 2])

col1.subheader("Average Recency in each segments")
recency_df = rfm_summary.sort_values(by='Avg. Recency', ascending=False)
fig = px.bar(recency_df, x='Avg. Recency', y='Segment')
col1.plotly_chart(fig, theme='streamlit', use_container_width=True)

col2.subheader("Average Monetary value in each segments")
monetary_df = rfm_summary.sort_values(by='Avg. Monetary', ascending=True)
fig = px.bar(monetary_df, x='Avg. Monetary', y='Segment')
col2.plotly_chart(fig, theme='streamlit', use_container_width=True)

# add column selection
default_var = "frequency"

if st.sidebar.button("frequency"):
    default_var = "frequency"
if st.sidebar.button("recency"):
    default_var = "recency"

options = rfm_df[['frequency', 'recency']].columns
col_selection = st.selectbox("Choose a variable:", options)

# visualize the scatter plot of recency vs monetary & frequency vs monetary
st.subheader(f"{col_selection} vs monetary")
fig = px.scatter(rfm_df, x=col_selection, y='monetary_value', color='Segment', hover_data=['customer_id'])
st.plotly_chart(fig, theme='streamlit', use_container_width=True)

# summary table of defined segments
st.subheader('RFM Segments: Statistics Summary')
st.dataframe(rfm_summary)

# last table: RFM Segments definition and recommendation >> WRONG
info = {
    'Segment': ['VIP', 'Very Loyal', 'Potential Loyalist', 'New Customers', 'Potential Customers', 'High risk to churn', 'Lost Customers'],
    'Characteristic': ['Bought recently, buy often and spend the most',
    'Buy on a regular basis. Responsive to promotions',
    'Recent customers with average frequency',
    'Bought most recently, but not often',
    'Recent shoppers, but haven\’t spent much',
    'Some time since they\’ve purchased. Need to bring them back!',
    'Last purchase was long back and low number of orders. May be lost']
}

st.subheader('RFM Segments Information')
st.dataframe(pd.DataFrame(info))

# END