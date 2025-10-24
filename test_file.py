import pandas as pd

# Path to your CSV file
csv_path = "historical_size_availability.csv"

# Column name you want to search in
column_name = "unique_size_id"

# Value (cell) you want to find occurrences of
target_value = "PROD-CF361A00_GIFTCARD-7500_25"

# Read CSV
df = pd.read_csv(csv_path)

# Count occurrences
occurrences = (df[column_name] == target_value).sum()

# Optionally, print all matching rows
matching_rows = df[df[column_name] == target_value]

print(f"Occurrences of '{target_value}' in column '{column_name}': {occurrences}")
print("\nSample matches:")
print(matching_rows.head())  # prints first few matches
