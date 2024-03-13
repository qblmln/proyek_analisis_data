import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style='dark')

# Helper function yang dibutuhkan untuk menyiapkan berbagai dataframe

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_estimated_delivery_date').agg({
        "order_id": "count",  # Menggunakan 'count' untuk menghitung jumlah order pada setiap tanggal
        "price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "estimated_order_count",  # Ubah nama kolom
        "price": "revenue"
    }, inplace=True)

    return daily_orders_df


def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name_english").order_item_id.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_byzipcode_df(df):
    byzipcode_df = df.groupby(by="customer_zip_code_prefix").customer_id.nunique().reset_index()
    byzipcode_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    
    return byzipcode_df

def create_bycity_df(df):
    bycity_df = df.groupby(by="customer_city").customer_id.nunique().reset_index()
    bycity_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    
    return bycity_df

def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    
    return bystate_df

def create_rfm_df(df):
    df_recency = df.groupby(by='customer_unique_id', as_index=False)['order_estimated_delivery_date'].max()
    df_recency.rename(columns={"order_estimated_delivery_date": "LastPurchaseDate"}, inplace=True)
    df_recency["LastPurchaseDate"] = df_recency["LastPurchaseDate"].dt.date
    recent_date = df['order_estimated_delivery_date'].dt.date.max()
    df_recency['recency'] = df_recency['LastPurchaseDate'].apply(lambda x: (recent_date - x).days)

    frequency_df = df.groupby(["customer_unique_id"]).agg({"order_id": "nunique"}).reset_index()
    frequency_df.rename(columns={"order_id": "frequency"}, inplace=True)

    monetary_df = df.groupby('customer_unique_id', as_index=False)['payment_value'].sum()
    monetary_df.rename(columns={"payment_value": "monetary"}, inplace=True)

    rfm_df = df_recency.merge(frequency_df, on='customer_unique_id') \
        .merge(monetary_df, on='customer_unique_id')

    rfm_df.drop('LastPurchaseDate', axis=1, inplace=True)
    
    return rfm_df

# Load cleaned data
all_df = pd.read_csv("all_data.csv")

datetime_columns = ["order_estimated_delivery_date"]

all_df.sort_values(by="order_estimated_delivery_date", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column], format='%Y-%m-%d')

#Filter data
min_date = all_df["order_estimated_delivery_date"].min()
max_date = all_df["order_estimated_delivery_date"].max()

with st.sidebar:
    # Menambahkan logo perusahaan
    # st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[(all_df["order_estimated_delivery_date"] >= str(start_date)) & 
                (all_df["order_estimated_delivery_date"] <= str(end_date))]

# st.dataframe(main_df)

# # Menyiapkan berbagai dataframe
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
byzipcode_df = create_byzipcode_df(main_df)
bycity_df = create_bycity_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)


# plot number of daily orders (2021)
st.header('E-Commerce Dashboard :sparkles:')
st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = total_orders = daily_orders_df.estimated_order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "AUD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_estimated_delivery_date"],
    daily_orders_df["estimated_order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)

ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)



# Product performance
st.subheader("Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="order_item_id", y="product_category_name_english", data=sum_order_items_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="order_item_id", y="product_category_name_english", data=sum_order_items_df.sort_values(by="order_item_id", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)

st.pyplot(fig)

# customer demographic
st.subheader("Customer Demographics")

fig, ax1 = plt.subplots(figsize=(20, 10))  # Hanya menggunakan satu subplot

# Plot untuk jumlah pelanggan berdasarkan negara bagian
sns.barplot(
    x="customer_count", 
    y="customer_state",
    data=bystate_df.sort_values(by="customer_count", ascending=False),
    hue="customer_state",  # Menetapkan hue ke variabel yang sama dengan y
    palette="deep",  # Menggunakan palet "deep" yang lebih tegas dan dominan
    legend=False,  # Menghilangkan legenda
    ax=ax1  # Menggunakan ax2 untuk subplot
)
ax1.set_title("Number of Customers by State", loc="center", fontsize=30)  # Mengatur judul plot
ax1.set_ylabel(None)
ax1.set_xlabel(None)
ax1.tick_params(axis='y', labelsize=20)
ax1.tick_params(axis='x', labelsize=15)

plt.tight_layout()  # Memastikan layout subplot yang rapi

# Tampilkan gambar di Streamlit
st.pyplot(fig)

# Best Customer Based on RFM Parameters
st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(45, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(y="recency", x="customer_unique_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])

ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=50)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35, rotation=30)

sns.barplot(y="frequency", x="customer_unique_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])

ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=50)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35, rotation=30)

sns.barplot(y="monetary", x="customer_unique_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=50)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35, rotation=30)

st.pyplot(fig)

st.caption('Copyright © Dicoding 2023') 