# recommender_engine.py
import data_recommender

def get_recommendations(seed_shoe, all_shoes_df):
    """
    Orchestrate recommendation flow: uses data_recommender (stage 1).
    Returns top 5 final recommendations (visual stage is skipped).
    """
    print("[recommender_engine]: Orchestrating recommendation flow...")
    top_20 = data_recommender.get_data_recommendations(seed_shoe, all_shoes_df, top_n=20)
    final_top_5 = top_20.head(5).reset_index(drop=True)

    # keep visual_similarity_score column present
    if "visual_similarity_score" not in final_top_5.columns:
        final_top_5["visual_similarity_score"] = 0.0

    print("[recommender_engine]: Flow complete. Returning top 5 from data stage.")
    return final_top_5

# recommender_engine.py (Add this function)

def get_recommendations_by_criteria(criteria, all_shoes_df):
    """Entry point for Chatbot Search Intents"""
    # 1. Filter
    filtered = data_recommender.get_filtered_recommendations(criteria, all_shoes_df, top_n=5)
    
    if filtered.empty:
        return pd.DataFrame()
        
    # 2. Add compatibility columns for UI
    filtered["data_similarity_score"] = 1.0
    filtered["visual_similarity_score"] = 0.0
    
    return filtered.head(5).reset_index(drop=True)
