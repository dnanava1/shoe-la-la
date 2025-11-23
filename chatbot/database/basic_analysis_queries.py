from .queries import get_connection
import pandas as pd

def get_basic_metrics():
    """Get basic overview metrics"""
    conn = get_connection()
    query = """
        SELECT
            COUNT(DISTINCT mp.main_product_id) as total_models,
            COUNT(DISTINCT cv.unique_color_id) as total_color_variants,
            COUNT(DISTINCT sv.unique_size_id) as total_size_variants,
            SUM(CASE WHEN p.available THEN 1 ELSE 0 END) as total_available_items,
            AVG(p.price) as average_price,
            MAX(p.price) as max_price,
            MIN(p.price) as min_price
        FROM main_products mp
        JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
        JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
        JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
        JOIN prices p ON sv.unique_size_id = p.unique_size_id;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_price_range_analysis():
    """Analyze price distribution across products"""
    conn = get_connection()
    query = """
        SELECT
            CASE
                WHEN p.price < 50 THEN 'Under $50'
                WHEN p.price BETWEEN 50 AND 100 THEN '$50-$100'
                WHEN p.price BETWEEN 100 AND 150 THEN '$100-$150'
                WHEN p.price BETWEEN 150 AND 200 THEN '$150-$200'
                ELSE 'Over $200'
            END as price_range,
            COUNT(*) as product_count,
            AVG(p.price) as avg_price_in_range
        FROM prices p
        WHERE p.available = true
        GROUP BY price_range
        ORDER BY MIN(p.price);
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_availability_analysis():
    """Analyze stock availability"""
    conn = get_connection()
    query = """
        SELECT
            mp.category,
            SUM(CASE WHEN p.available THEN 1 ELSE 0 END) as available_count,
            COUNT(*) as total_listings,
            ROUND(SUM(CASE WHEN p.available THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as availability_percent
        FROM main_products mp
        JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
        JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
        JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
        JOIN prices p ON sv.unique_size_id = p.unique_size_id
        GROUP BY mp.category
        ORDER BY availability_percent DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_top_collections():
    """Get top collections by model count - limit to top 9 and group others"""
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
                COUNT(DISTINCT mp.main_product_id) as model_count,
                AVG(p.price) as avg_price,
                SUM(CASE WHEN p.available THEN 1 ELSE 0 END) as total_available
            FROM main_products mp
            JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
            JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
            JOIN size_variants sv ON cv.unique_color_id = sv.unique_color_id
            JOIN prices p ON sv.unique_size_id = p.unique_size_id
            WHERE p.available = true
            GROUP BY collection
        ),
        ranked_collections AS (
            SELECT *,
                   ROW_NUMBER() OVER (ORDER BY model_count DESC) as rank
            FROM collection_data
        )
        SELECT
            CASE WHEN rank <= 9 THEN collection ELSE 'Other Collections' END as collection,
            SUM(model_count) as model_count,
            AVG(avg_price) as avg_price,
            SUM(total_available) as total_available
        FROM ranked_collections
        GROUP BY CASE WHEN rank <= 9 THEN collection ELSE 'Other Collections' END
        ORDER BY model_count DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_category_distribution():
    """Get distribution of products by category - top 9 categories"""
    conn = get_connection()
    query = """
        WITH category_data AS (
            SELECT
                mp.category,
                COUNT(DISTINCT mp.main_product_id) as model_count,
                COUNT(DISTINCT cv.unique_color_id) as color_variant_count,
                ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT mp.main_product_id) DESC) as rank
            FROM main_products mp
            JOIN fit_variants fv ON mp.main_product_id = fv.main_product_id
            JOIN color_variants cv ON fv.unique_fit_id = cv.unique_fit_id
            GROUP BY mp.category
        )
        SELECT
            CASE WHEN rank <= 9 THEN category ELSE 'Other Categories' END as category,
            SUM(model_count) as model_count,
            SUM(color_variant_count) as color_variant_count
        FROM category_data
        GROUP BY CASE WHEN rank <= 9 THEN category ELSE 'Other Categories' END
        ORDER BY model_count DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df