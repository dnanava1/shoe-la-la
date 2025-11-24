# data_manager.py
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def _process_category_string(category_str):
    gender = 'unisex'
    clean_category = 'general'
    if not category_str or pd.isna(category_str):
        return gender, clean_category

    cat = str(category_str).lower()
    if "men" in cat:
        gender = 'men'
    elif "women" in cat:
        gender = 'women'

    clean_category = (
        cat.replace("men's", "")
           .replace("women's", "")
           .replace("shoes", "")
           .replace("shoe", "")
           .strip()
    )
    if clean_category == "":
        clean_category = "general"

    return gender, clean_category


def _split_color_string(color_str):
    if not color_str or pd.isna(color_str):
        return []
    s = str(color_str)
    if "/" in s:
        parts = [p.strip().lower() for p in s.split("/") if p.strip()]
    else:
        parts = [p.strip().lower() for p in s.split(",") if p.strip()]
    return parts


def get_db_engine():
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        raise RuntimeError("Missing DB credentials in environment (.env)")

    conn_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(conn_str)
    print("[data_manager]: Connected to AWS RDS (Postgres).")
    return engine


def load_shoe_database():
    """
    Loads and flattens normalized tables into a dataframe of color-variant-level rows.
    Each row corresponds to one color_variant (unique_color_id) with most-recent price.
    Returned columns include:
      - shoe_id (unique_color_id)
      - main_product_id
      - name
      - price (price from latest capture_timestamp)
      - latest_capture_timestamp (Timestamp of the price used)
      - image_url (color_image_url)
      - gender
      - category
      - colors (list)
      - tag
      - base_url
      - available (based on latest log if present)
      - original_price, discount_percent, change_type (if present)
    """
    engine = get_db_engine()

    # Read normalized tables
    main_df = pd.read_sql("SELECT * FROM main_products", engine)
    fit_df = pd.read_sql("SELECT * FROM fit_variants", engine)
    color_df = pd.read_sql("SELECT * FROM color_variants", engine)
    size_df = pd.read_sql("SELECT * FROM size_variants", engine)
    prices_df = pd.read_sql("SELECT * FROM prices", engine)

    # --- Build latest-price-per-unique_color_id ---
    # Merge sizes -> prices to get per-size logs annotated with unique_color_id
    size_prices = size_df.merge(prices_df, on="unique_size_id", how="left")

    # Make sure capture_timestamp is a proper datetime
    if "capture_timestamp" in size_prices.columns:
        size_prices["capture_timestamp"] = pd.to_datetime(size_prices["capture_timestamp"], errors="coerce")
    else:
        # if not present, create NaT so latest selection will be ambiguous
        size_prices["capture_timestamp"] = pd.NaT

    # Drop rows with no unique_color_id (defensive)
    size_prices = size_prices[size_prices["unique_color_id"].notna()]

    # For each unique_color_id, pick the row with the max capture_timestamp (latest)
    # We'll keep price, available, original_price, discount_percent, change_type, and timestamp
    idx = size_prices.groupby("unique_color_id")["capture_timestamp"].idxmax()
    # idx may contain NaN if capture_timestamp all NaT for that color. Drop NaNs then handle fallback.
    idx = idx.dropna().astype(int, errors="ignore")

    latest_logs = size_prices.loc[idx].copy()

    # Sometimes there are colors with no logs at all; for those we won't have a latest log
    # Create price_lookup keyed by unique_color_id with columns: price, available, original_price, discount_percent, change_type, latest_capture_timestamp
    if not latest_logs.empty:
        latest_logs = latest_logs.rename(columns={
            "price": "latest_price",
            "available": "latest_available",
            "original_price": "latest_original_price",
            "discount_percent": "latest_discount_percent",
            "change_type": "latest_change_type",
            "capture_timestamp": "latest_capture_timestamp"
        })
        price_lookup = latest_logs[[
            "unique_color_id",
            "latest_price",
            "latest_available",
            "latest_original_price",
            "latest_discount_percent",
            "latest_change_type",
            "latest_capture_timestamp"
        ]].drop_duplicates(subset=["unique_color_id"])
    else:
        # empty DataFrame with expected columns
        price_lookup = pd.DataFrame(columns=[
            "unique_color_id",
            "latest_price",
            "latest_available",
            "latest_original_price",
            "latest_discount_percent",
            "latest_change_type",
            "latest_capture_timestamp"
        ])

    # --- Join color_variants -> fit_variants -> main_products ---
    color_fit = color_df.merge(fit_df, on="unique_fit_id", how="left")
    merged = color_fit.merge(main_df, on="main_product_id", how="left")

    # Add latest price info (if any)
    merged = merged.merge(price_lookup, on="unique_color_id", how="left")

    # --- Build processed rows (one row per unique_color_id / color-variant) ---
    processed = []
    for _, r in merged.iterrows():
        shoe_id = r.get("unique_color_id")
        main_product_id = r.get("main_product_id")
        # name column could be 'name' or 'product_name', try both
        name = r.get("name") or r.get("product_name") or ""
        raw_category = r.get("category", "")
        gender, clean_category = _process_category_string(raw_category)
        color_name_raw = r.get("color_name", "")
        colors = _split_color_string(color_name_raw)

        # Prefer the latest price if present
        latest_price = r.get("latest_price")
        latest_ts = r.get("latest_capture_timestamp")
        available = r.get("latest_available") if "latest_available" in r else None
        orig_price = r.get("latest_original_price") if "latest_original_price" in r else None
        discount = r.get("latest_discount_percent") if "latest_discount_percent" in r else None
        change_type = r.get("latest_change_type") if "latest_change_type" in r else None

        # If latest_price is NaN/None, fallback to NULL/None
        price_val = float(latest_price) if pd.notna(latest_price) else None

        image_url = r.get("color_image_url") or r.get("image_url") or None
        tag = r.get("tag") if "tag" in r else None
        base_url = r.get("base_url") if "base_url" in r else None

        processed.append({
            "shoe_id": shoe_id,
            "main_product_id": main_product_id,
            "name": name,
            "price": price_val,
            "latest_capture_timestamp": pd.to_datetime(latest_ts) if pd.notna(latest_ts) else pd.NaT,
            "available": bool(available) if pd.notna(available) else None,
            "original_price": float(orig_price) if pd.notna(orig_price) else None,
            "discount_percent": int(discount) if pd.notna(discount) else None,
            "change_type": change_type,
            "image_url": image_url,
            "gender": gender,
            "category": clean_category,
            "colors": colors,
            "tag": tag,
            "base_url": base_url
        })

    all_shoes_df = pd.DataFrame(processed)

    # Clean
    all_shoes_df = all_shoes_df.dropna(subset=["shoe_id", "name"]).reset_index(drop=True)

    print(f"[data_manager]: Prepared {len(all_shoes_df)} color-variant rows for recommender (with latest timestamps).")
    return all_shoes_df


if __name__ == "__main__":
    df = load_shoe_database()
    print(df.head())
