import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def get_category(gender):
    if gender and gender.lower() == 'men':
        return "Men's Shoes"
    elif gender and gender.lower() == 'women':
        return "Women's Shoes"
    else:
        return "Unisex"

def get_size_label(cursor, shoe_size, gender):
    if not shoe_size:
        return None

    shoe_size_str = str(shoe_size)
    if gender and gender.lower() == 'men':
        cursor.execute(
            "SELECT size_label FROM size_variants WHERE size::text = %s LIMIT 1;",
            (shoe_size_str,)
        )
    else:
        cursor.execute(
            "SELECT size_label FROM size_variants WHERE size_label LIKE %s LIMIT 1;",
            (f"%W {shoe_size_str}%",)
        )
    row = cursor.fetchone()
    return row[0] if row else None

def handle_view_details_query(intent_json):
    conn = get_connection()
    cur = conn.cursor()

    shoe_name = intent_json.get('shoe_name', '')
    constraints = intent_json.get('constraints', {})
    color = constraints.get('shoe_color', '')
    size = constraints.get('shoe_size')
    gender = constraints.get('gender')

    category = get_category(gender)
    size_label = get_size_label(cur, size, gender) if size else None

    query = """
        SELECT
            mp.name AS shoe_name,
            cv.color_name,
            sv.size_label,
            p.price,
            p.original_price,
            p.discount_percent,
            cv.color_url
        FROM main_products mp
        JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
        JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
        JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
        JOIN prices p ON sv.unique_size_id = p.unique_size_id
        WHERE mp.name ILIKE %s
          AND cv.color_name ILIKE %s
          AND mp.category = %s
    """
    params = [f"%{shoe_name}%", f"%{color}%", category]

    if size_label:
        query += " AND sv.size_label = %s"
        params.append(size_label)

    query += " ORDER BY p.capture_timestamp DESC LIMIT 1;"

    cur.execute(query, params)
    result = cur.fetchone()

    cur.close()
    conn.close()

    return result