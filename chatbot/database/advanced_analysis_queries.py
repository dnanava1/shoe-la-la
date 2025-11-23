from .queries import get_connection
import pandas as pd

def get_price_trend_analysis():
    """Analyze price trends for different collections - exclude 'Other' from premium metrics"""
    conn = get_connection()
    query = """
        WITH collection_data AS (
            SELECT
                CASE
                    WHEN mp.name ILIKE '%jordan%' THEN 'Jordan'
                    WHEN mp.name ILIKE '%air force%' THEN 'Air Force'
                    WHEN mp.name ILIKE '%air max%' THEN 'Air Max'
                    WHEN mp.name ILIKE '%dunk%' THEN 'Dunk'
                    WHEN mp.name ILIKE '%vomero%' THEN 'Vomero'
                    WHEN mp.name ILIKE '%mercurial%' THEN 'Mercurial'
                    WHEN mp.name ILIKE '%pegasus%' THEN 'Pegasus'
                    WHEN mp.name ILIKE '%blazer%' THEN 'Blazer'
                    WHEN mp.name ILIKE '%cortez%' THEN 'Cortez'
                    ELSE 'Other'
                END as collection,
                AVG(p.price) as avg_price,
                MIN(p.price) as min_price,
                MAX(p.price) as max_price,
                COUNT(*) as total_listings
            FROM main_products mp
            JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
            JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
            JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
            JOIN prices p ON sv.unique_size_id = p.unique_size_id
            WHERE p.available = true
            GROUP BY collection
        )
        SELECT * FROM collection_data
        ORDER BY avg_price DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_size_availability_heatmap():
    """Which sizes are most available/rare for popular models"""
    conn = get_connection()
    query = """
        WITH popular_models AS (
            SELECT mp.main_product_id, mp.name
            FROM main_products mp
            JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
            JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
            GROUP BY mp.main_product_id, mp.name
            ORDER BY COUNT(DISTINCT cv.unique_color_id) DESC
            LIMIT 8
        )
        SELECT
            pm.name as model,
            sv.size,
            COUNT(DISTINCT cv.unique_color_id) as color_variants_available,
            AVG(p.price) as avg_price,
            SUM(CASE WHEN p.available THEN 1 ELSE 0 END) as currently_available,
            MIN(p.price) as lowest_price_available
        FROM popular_models pm
        JOIN fit_variants fv ON pm.main_product_id = fv.main_product_id
        JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
        JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
        JOIN prices p ON sv.unique_size_id = p.unique_size_id
        GROUP BY pm.name, sv.size
        ORDER BY pm.name, sv.size;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_discount_analysis():
    """Find products with actual discounts"""
    conn = get_connection()
    query = """
        SELECT
            mp.name,
            cv.color_name,
            sv.size,
            p.price,
            p.original_price,
            p.discount_percent,
            mp.category
        FROM main_products mp
        JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
        JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
        JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
        JOIN prices p ON sv.unique_size_id = p.unique_size_id
        WHERE p.discount_percent > 0
          AND p.available = true
        ORDER BY p.discount_percent DESC
        LIMIT 20;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_color_popularity_impact():
    """How color affects price and availability"""
    conn = get_connection()
    query = """
        SELECT
            cv.color_name,
            COUNT(DISTINCT mp.main_product_id) as models_available,
            AVG(p.price) as avg_price,
            COUNT(DISTINCT cv.unique_color_id) as total_variants,
            SUM(CASE WHEN p.available THEN 1 ELSE 0 END) as currently_available
        FROM main_products mp
        JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
        JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
        JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
        JOIN prices p ON sv.unique_size_id = p.unique_size_id
        WHERE cv.color_name != 'Default Color'
        GROUP BY cv.color_name
        HAVING COUNT(*) > 2
        ORDER BY avg_price DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_rare_finds_analysis():
    """Identify rare/limited edition shoes"""
    conn = get_connection()
    query = """
        SELECT
            mp.name,
            cv.color_name,
            COUNT(DISTINCT sv.size) as sizes_available,
            AVG(p.price) as avg_price,
            MIN(p.price) as lowest_price,
            MAX(p.price) as highest_price,
            SUM(CASE WHEN p.available THEN 1 ELSE 0 END) as total_available
        FROM main_products mp
        JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
        JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
        JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
        JOIN prices p ON sv.unique_size_id = p.unique_size_id
        WHERE mp.category IN ('Men''s Shoes', 'Women''s Shoes')
        GROUP BY mp.name, cv.color_name
        HAVING COUNT(DISTINCT sv.size) <= 5  -- Limited size availability
           AND SUM(CASE WHEN p.available THEN 1 ELSE 0 END) <= 10  -- Low stock
        ORDER BY avg_price DESC
        LIMIT 15;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_best_value_recommendations():
    """Find shoes with best value (multiple color options, good pricing)"""
    conn = get_connection()
    query = """
        WITH value_analysis AS (
            SELECT
                mp.name,
                mp.category,
                COUNT(DISTINCT cv.color_name) as color_options,
                COUNT(DISTINCT sv.size) as size_options,
                AVG(p.price) as avg_price,
                MIN(p.price) as min_price,
                SUM(CASE WHEN p.available THEN 1 ELSE 0 END) as total_available,
                -- Get the first available image URL for this product
                (SELECT cv2.color_image_url
                 FROM color_variants cv2
                 JOIN fit_variants fv2 ON cv2.unique_fit_id = fv2.unique_fit_id
                 WHERE fv2.main_product_id = mp.main_product_id
                   AND cv2.color_image_url IS NOT NULL
                   AND cv2.color_image_url != ''
                 LIMIT 1) as sample_image_url,
                -- Value score: more options + lower price + good availability
                (COUNT(DISTINCT cv.color_name) * 0.4 +
                 COUNT(DISTINCT sv.size) * 0.3 +
                 (200 - LEAST(AVG(p.price), 200)) / 200 * 0.3) as value_score
            FROM main_products mp
            JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
            JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
            JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
            JOIN prices p ON sv.unique_size_id = p.unique_size_id
            WHERE p.available = true
              AND mp.category IN ('Men''s Shoes', 'Women''s Shoes', 'Big Kids'' Shoes')
            GROUP BY mp.name, mp.category, mp.main_product_id
            HAVING AVG(p.price) BETWEEN 50 AND 250  -- Reasonable price range
        )
        SELECT * FROM value_analysis
        ORDER BY value_score DESC
        LIMIT 12;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_category_price_analysis():
    """Price analysis by category"""
    conn = get_connection()
    query = """
        SELECT
            mp.category,
            COUNT(DISTINCT mp.main_product_id) as unique_models,
            AVG(p.price) as avg_price,
            MIN(p.price) as min_price,
            MAX(p.price) as max_price,
            SUM(CASE WHEN p.available THEN 1 ELSE 0 END) as total_available
        FROM main_products mp
        JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
        JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
        JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
        JOIN prices p ON sv.unique_size_id = p.unique_size_id
        GROUP BY mp.category
        ORDER BY avg_price DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df