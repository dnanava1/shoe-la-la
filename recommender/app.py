# app.py
import pandas as pd
import data_manager
import recommender_engine
import warnings
import visualizer  # 👈 NEW import

def run_app(user_query_name):
    warnings.filterwarnings('ignore')
    print("[app]: Starting Clickless AI Recommendation System...")

    # Load database (from RDS)
    all_shoes_df = data_manager.load_shoe_database()
    if all_shoes_df.empty:
        print("[app]: No data available. Exiting.")
        return

    print(f"[app]: Loaded {len(all_shoes_df)} color-variant rows.\n")

    # ---- USER QUERY ----
    # user_query_name = "Pegasus"   # You can dynamically set this via chatbot input later
    print(f"[app]: Searching for seed shoe containing '{user_query_name}'...")

    # Case-insensitive partial name match
    seed_rows = all_shoes_df[all_shoes_df['name'].str.contains(user_query_name, case=False, na=False)]

    if seed_rows.empty:
        print(f"[app]: Seed shoe '{user_query_name}' not found in database.")
        return

    # Choose the first matching color variant as seed
    seed_shoe = seed_rows.iloc[0]
    print(f"[app]: Found seed shoe: '{seed_shoe['name']}' (ID: {seed_shoe['shoe_id']})")

    # ---- RECOMMENDATION LOGIC ----
    final_recommendations = recommender_engine.get_recommendations(seed_shoe, all_shoes_df)

    # ---- DISPLAY RESULTS (CLI) ----
    print("\n--- FINAL RECOMMENDATIONS ---")
    print(f"Because you liked the '{seed_shoe['name']}', you might also like:\n")

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1200)

    display_cols = [
        'shoe_id', 'name', 'category', 'price',
        'name_similarity_score', 'color_similarity_score', 'price_similarity_score',
        'final_score'
    ]
    available_cols = [c for c in display_cols if c in final_recommendations.columns]
    print(final_recommendations[available_cols].head(10).to_string(index=False))

    # ---- VISUALIZE RESULTS (NEW PART) ----
#     visualizer.show_recommendations(seed_shoe, final_recommendations)  # 👈 ADD THIS LINE HERE

    return final_recommendations


if __name__ == "__main__":
    run_app()
