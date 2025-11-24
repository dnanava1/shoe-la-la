import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database credentials
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", 5432)

# Connect to RDS
conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    port=DB_PORT
)
cursor = conn.cursor()

# ------------------------------------
# Get row counts for all main tables
# ------------------------------------
tables = ["main_products", "fit_variants", "color_variants", "size_variants", "prices"]

row_counts = {}
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    count = cursor.fetchone()[0]
    row_counts[table] = count

# Convert to DataFrame for better display
row_counts_df = pd.DataFrame(list(row_counts.items()), columns=["Table Name", "Row Count"])
print("\n📊 Table Row Counts:")
print(row_counts_df.to_string(index=False))

# Optional: visualize
import matplotlib.pyplot as plt
plt.figure(figsize=(7, 4))
plt.bar(row_counts_df["Table Name"], row_counts_df["Row Count"], color="skyblue")
plt.title("Row Count per Table")
plt.xlabel("Table Name")
plt.ylabel("Number of Rows")
plt.tight_layout()
plt.show()

# Close connection
cursor.close()
conn.close()
