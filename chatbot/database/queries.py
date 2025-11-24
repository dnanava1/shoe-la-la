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

def find_unique_size_id(shoe_name, fit_name, color_name, size):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT sv.unique_size_id
        FROM main_products mp
        JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
        JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
        JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
        WHERE mp.name ILIKE %s
          AND fv.fit_name ILIKE %s
          AND cv.color_name ILIKE %s
          AND sv.size = %s
        LIMIT 1;
    """

    cur.execute(query, (f"%{shoe_name}%", f"%{fit_name}%", f"%{color_name}%", size))
    row = cur.fetchone()

    cur.close()
    conn.close()

    return row[0] if row else None

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
            cv.color_url,
            cv.color_image_url  -- Added image URL
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

def get_shoe_image_url(shoe_name, color):
    """
    Get the image URL for a specific shoe and color combination
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        SELECT cv.color_image_url
        FROM color_variants cv
        JOIN fit_variants fv ON cv.unique_fit_id = fv.unique_fit_id
        JOIN main_products mp ON fv.main_product_id = mp.main_product_id
        WHERE mp.name ILIKE %s
        AND cv.color_name ILIKE %s
        AND cv.color_image_url IS NOT NULL
        AND cv.color_image_url != ''
        LIMIT 1
        """

        cursor.execute(query, (f'%{shoe_name}%', f'%{color}%'))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return result[0] if result else None

    except Exception as e:
        print(f"Error getting shoe image: {e}")
        return None

# Additional helper function for watchlist operations
def get_shoe_details_by_size_id(unique_size_id):
    """
    Get complete shoe details by unique_size_id for watchlist display
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            mp.name,
            cv.color_name,
            sv.size_label,
            p.price,
            p.original_price,
            p.discount_percent,
            cv.color_url,
            cv.color_image_url
        FROM size_variants sv
        JOIN color_variants cv ON sv.unique_color_id = cv.unique_color_id
        JOIN fit_variants fv ON cv.unique_fit_id = fv.unique_fit_id
        JOIN main_products mp ON fv.main_product_id = mp.main_product_id
        JOIN prices p ON sv.unique_size_id = p.unique_size_id
        WHERE sv.unique_size_id = %s
        AND p.available = true
        ORDER BY p.capture_timestamp DESC
        LIMIT 1
        """

        cursor.execute(query, (unique_size_id,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return {
                'name': result[0],
                'color': result[1],
                'size_label': result[2],
                'price': result[3],
                'original_price': result[4],
                'discount_percent': result[5],
                'color_url': result[6],
                'image_url': result[7]
            }
        return None

    except Exception as e:
        print(f"Error getting shoe details by size ID: {e}")
        return None


def get_shoe_details_by_color_id(unique_color_id):
    """
    Get complete shoe details by unique_color_id
    Returns details for the first available size
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            mp.name,
            cv.color_name,
            sv.size_label,
            p.price,
            p.original_price,
            p.discount_percent,
            cv.color_url,
            cv.color_image_url,
            sv.unique_size_id
        FROM color_variants cv
        JOIN fit_variants fv ON cv.unique_fit_id = fv.unique_fit_id
        JOIN main_products mp ON fv.main_product_id = mp.main_product_id
        JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
        JOIN prices p ON sv.unique_size_id = p.unique_size_id
        WHERE cv.unique_color_id = %s
        AND p.available = true
        ORDER BY p.capture_timestamp DESC
        LIMIT 1
        """

        cursor.execute(query, (unique_color_id,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return {
                'name': result[0],
                'color': result[1],
                'size_label': result[2],
                'price': result[3],
                'original_price': result[4],
                'discount_percent': result[5],
                'color_url': result[6],
                'image_url': result[7],
                'unique_size_id': result[8]
            }
        return None

    except Exception as e:
        print(f"Error getting shoe details by color ID: {e}")
        return None