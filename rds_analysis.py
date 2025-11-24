import os
import pandas as pd
import matplotlib.pyplot as plt
import psycopg2
from dotenv import load_dotenv

# ------------------------------------
# Load environment variables
# ------------------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", 5432)

# ------------------------------------
# Connect to RDS
# ------------------------------------
conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    port=DB_PORT
)

print("✅ Connected to RDS successfully")

# ------------------------------------
# Fetch data
# ------------------------------------
query = """
SELECT mp.name AS shoe_name,
       mp.category,
       p.price,
       p.original_price,
       p.discount_percent,
       p.available,
       p.capture_timestamp
FROM prices p
JOIN main_products mp
    ON SPLIT_PART(p.unique_size_id, '_', 1) = mp.main_product_id
WHERE p.capture_timestamp >= NOW() - INTERVAL '30 days'
"""
df = pd.read_sql(query, conn)
conn.close()
print("🔒 Connection closed.")

# ------------------------------------
# Data overview
# ------------------------------------
print("\n📊 Data Overview:")
print(df.head())
print(f"\nTotal records: {len(df)}")

# Convert timestamps and clean data
df['capture_timestamp'] = pd.to_datetime(df['capture_timestamp'])
df['available'] = df['available'].astype(int)
df['discount_percent'] = pd.to_numeric(df['discount_percent'], errors='coerce').fillna(0)

# ------------------------------------
# 1️⃣ Discount Distribution
# ------------------------------------
plt.figure(figsize=(8,5))
df['discount_percent'].hist(bins=20, color='lightgreen', edgecolor='black')
plt.title("Distribution of Discounts (%)")
plt.xlabel("Discount Percent")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()

# ------------------------------------
# 2️⃣ Availability Trend Over Time
# ------------------------------------
availability_trend = df.groupby(df['capture_timestamp'].dt.date)['available'].mean()
plt.figure(figsize=(10,5))
availability_trend.plot(marker='o', color='orange')
plt.title("Average Product Availability Over Time")
plt.xlabel("Date")
plt.ylabel("Average Availability (1=Available, 0=Not)")
plt.tight_layout()
plt.show()

# ------------------------------------
# 3️⃣ Average Price Trend (Last 30 Days)
# ------------------------------------
daily_avg_price = df.groupby(df['capture_timestamp'].dt.date)['price'].mean()
plt.figure(figsize=(10,5))
daily_avg_price.plot(marker='o', color='purple')
plt.title("Average Price Trend (Last 30 Days)")
plt.xlabel("Date")
plt.ylabel("Average Price ($)")
plt.tight_layout()
plt.show()

# ------------------------------------
# 4️⃣ Top 10 Most Discounted Shoes (Max Discount)
# ------------------------------------
max_discounts = df.groupby('shoe_name')['discount_percent'].max().sort_values(ascending=False).head(10)
plt.figure(figsize=(10,5))
max_discounts.plot(kind='bar', color='salmon')
plt.title("Top 10 Most Discounted Shoes (Max Discount %)")
plt.xlabel("Shoe Name")
plt.ylabel("Max Discount (%)")
plt.tight_layout()
plt.show()

# ------------------------------------
# 5️⃣ Price Volatility (Standard Deviation)
# ------------------------------------
price_volatility = df.groupby('shoe_name')['price'].std().dropna().sort_values(ascending=False).head(10)
plt.figure(figsize=(10,5))
price_volatility.plot(kind='bar', color='deepskyblue')
plt.title("Top 10 Shoes with Highest Price Volatility")
plt.xlabel("Shoe Name")
plt.ylabel("Price Standard Deviation ($)")
plt.tight_layout()
plt.show()

# ------------------------------------
# 6️⃣ Restock Frequency Analysis
# ------------------------------------
# Detect restocks: available goes from 0 → 1
df_sorted = df.sort_values(['shoe_name', 'capture_timestamp'])
df_sorted['prev_available'] = df_sorted.groupby('shoe_name')['available'].shift(1)
df_sorted['restock'] = (df_sorted['available'] == 1) & (df_sorted['prev_available'] == 0)
restock_counts = df_sorted.groupby('shoe_name')['restock'].sum().sort_values(ascending=False).head(10)

plt.figure(figsize=(10,5))
restock_counts.plot(kind='bar', color='limegreen')
plt.title("Top 10 Most Frequently Restocked Shoes")
plt.xlabel("Shoe Name")
plt.ylabel("Restock Count (0→1 transitions)")
plt.tight_layout()
plt.show()

# ------------------------------------
# 7️⃣ Average Discount by Category
# ------------------------------------
# ------------------------------------
# 7️⃣ Average Discount by Category (Improved Visualization)
# ------------------------------------
if 'category' in df.columns:
    # Compute mean discount and take top 10
    avg_discount_by_cat = (
        df.groupby('category')['discount_percent']
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    plt.figure(figsize=(10, 5))
    avg_discount_by_cat.plot(kind='bar', color='cornflowerblue')

    plt.title("Average Discount by Category (Top 10)")
    plt.xlabel("Category")
    plt.ylabel("Average Discount (%)")

    # Rotate labels and improve spacing
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.tight_layout()
    plt.show()
else:
    print("⚠️ 'category' column not found — skipping category-based analysis.")
