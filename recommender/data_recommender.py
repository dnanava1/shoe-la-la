# data_recommender.py
import pandas as pd
import numpy as np

# Prefer jellyfish for name similarity, fallback to SequenceMatcher
try:
    import jellyfish

    def _name_similarity(a, b):
        if not a or not b:
            return 0.0
        return jellyfish.jaro_winkler_similarity(str(a).lower(), str(b).lower())
except Exception:
    from difflib import SequenceMatcher

    def _name_similarity(a, b):
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


def _calculate_color_similarity(seed_colors, candidate_colors):
    """
    (Internal Helper) Calculates a weighted score based on color list.
    - seed_colors: ['pale ivory', 'fir', 'coconut milk']
    - candidate_colors: ['pale ivory', 'white', 'black']
    """
    if not seed_colors or not candidate_colors:
        return 0.0

    score = 0.0

    # Normalize to lowercase
    seed_colors_norm = [c.lower() for c in seed_colors]
    candidate_colors_norm = [c.lower() for c in candidate_colors]

    # 1. Primary Color Match (Weight: 70%)
    # Heavy emphasis on the first color
    try:
        if seed_colors_norm[0] == candidate_colors_norm[0]:
            score += 0.7
    except IndexError:
        pass

    # 2. Overall Palette Match (Weight: 30%)
    seed_set = set(seed_colors_norm)
    candidate_set = set(candidate_colors_norm)
    try:
        jaccard_sim = len(seed_set.intersection(candidate_set)) / len(seed_set.union(candidate_set))
        score += jaccard_sim * 0.3
    except ZeroDivisionError:
        pass

    return min(1.0, score)


def _calculate_data_similarity(seed_shoe, candidate_shoe):
    """
    Calculates a weighted similarity score based on:
     - Color (40%)
     - Gender (20%)
     - Price (20%) -- linear decay, 1.0 when same price, 0.0 at $75 diff
     - Category (10%)
     - Name similarity (10%)
    """
    total_score = 0.0

    if(seed_shoe.get("name", "") == candidate_shoe.get("name", "")):
        return 0.1

    # 1. Color Score (Weight: 40%)
    color_score = _calculate_color_similarity(seed_shoe.get("colors", []), candidate_shoe.get("colors", []))
    total_score += color_score * 0.25

    # 2. Gender Score (Weight: 20%)
    seed_gender = str(seed_shoe.get("gender", "unisex")).lower()
    cand_gender = str(candidate_shoe.get("gender", "unisex")).lower()
    if seed_gender == cand_gender:
        total_score += 0.3
    elif seed_gender == "unisex" or cand_gender == "unisex":
        total_score += 0.1

    # 3. Price Score (Weight: 20%)
    try:
        seed_price = float(seed_shoe.get("price", np.nan))
        cand_price = float(candidate_shoe.get("price", np.nan))
        price_diff = abs(seed_price - cand_price)
    except Exception:
        price_diff = np.nan

    if np.isnan(price_diff):
        price_score = 0.0
    else:
        price_score = max(0.0, 1.0 - (price_diff / 75.0))
        price_score = min(1.0, price_score)
    total_score += price_score * 0.25

    # 4. Category Score (Weight: 10%)
    if str(seed_shoe.get("category", "")).lower() == str(candidate_shoe.get("category", "")).lower():
        total_score += 0.1

    # 5. Name Similarity (Weight: 10%)
    name_score = _name_similarity(seed_shoe.get("name", ""), candidate_shoe.get("name", ""))
    total_score += name_score * 0.1

    return round(total_score, 6)


def get_data_recommendations(seed_shoe, all_shoes_df, top_n=20):
    """
    STAGE 1: Filters the entire database to the top_n most
    similar items based on data features.

    Args:
        seed_shoe (pd.Series or dict): The seed shoe (single row).
        all_shoes_df (pd.DataFrame): The entire database of shoes (one row per color variant).
        top_n (int): The number of recommendations to return.

    Returns:
        pd.DataFrame: A DataFrame of the top_n most similar shoes,
                      with 'data_similarity_score' and 'visual_similarity_score'.
    """
    print("[data_recommender]: Starting Stage 1 filter (with full color-aware logic)...")

    # Normalize seed_shoe to dict
    if isinstance(seed_shoe, pd.Series):
        seed = seed_shoe.to_dict()
    elif isinstance(seed_shoe, dict):
        seed = seed_shoe
    else:
        raise ValueError("seed_shoe must be a pandas Series or dict")

    # Score every candidate row
    def _score_row(row):
        candidate = {
            "shoe_id": row.get("shoe_id"),
            "name": row.get("name"),
            "category": row.get("category"),
            "gender": row.get("gender"),
            "colors": row.get("colors") if isinstance(row.get("colors"), list) else [],
            "price": row.get("price")
        }
        return _calculate_data_similarity(seed, candidate)

    scores = all_shoes_df.apply(_score_row, axis=1)

    recommendations_df = all_shoes_df.copy().reset_index(drop=True)
    recommendations_df["data_similarity_score"] = scores
    # visual stage not used: keep column for compatibility
    recommendations_df["visual_similarity_score"] = 0.0

    # Exclude seed itself (by shoe_id if present)
    seed_id = seed.get("shoe_id")
    if seed_id is not None:
        recommendations_df = recommendations_df[recommendations_df["shoe_id"] != seed_id]
    else:
        # fallback: remove rows with same name and price
        recommendations_df = recommendations_df[~(
            (recommendations_df["name"] == seed.get("name")) &
            (recommendations_df["price"] == seed.get("price"))
        )]

    # Sort descending and return top_n
    top_recommendations = recommendations_df.sort_values(by="data_similarity_score", ascending=False).head(top_n).reset_index(drop=True)

    print(f"[data_recommender]: Found {len(top_recommendations)} data-similar shoes.")
    return top_recommendations
# data_recommender.py (Add this function)

def get_filtered_recommendations(criteria, all_shoes_df, top_n=20):
    print(f"[data_recommender]: Filtering with criteria: {criteria}")
    df = all_shoes_df.copy()

    # Price Filter
    if criteria.get("max_price"):
        try:
            df = df[df["price"] <= float(criteria["max_price"])]
        except: pass
        
    # Gender Filter
    if criteria.get("gender"):
        target = criteria["gender"].lower()
        df = df[df["gender"].isin([target, "unisex"])]

    # Color Filter (Fuzzy)
    if criteria.get("color"):
        target = criteria["color"].lower()
        df = df[df["colors"].apply(lambda x: any(target in c.lower() for c in x) if isinstance(x, list) else False)]

    # Query Filter
    if criteria.get("query"):
        q = criteria["query"].lower()
        df = df[df["name"].str.lower().str.contains(q) | df["category"].str.lower().str.contains(q)]

    if df.empty: return pd.DataFrame()

    # Sort by Availability then Newest
    sort_cols = [c for c in ["available", "latest_capture_timestamp"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols, ascending=[False, False])
    
    return df.head(top_n).reset_index(drop=True)