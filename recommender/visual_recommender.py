import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity  # You may need to run: pip install scikit-learn

# --- This simulates our custom CBIR model ---
# In a real project, this would be a loaded .h5 or .pkl file
EMBEDDING_REGISTRY = {
    'pegasus40.jpg': [0.1, 0.9, 0.2, 0.4],  # High "runner" & "comfort" features
    'airmax90.jpg': [0.8, 0.2, 0.7, 0.1],  # High "lifestyle" & "classic" features
    'zoomfly5.jpg': [0.2, 0.8, 0.3, 0.5],  # Visually similar to Pegasus 40
    'af1.jpg': [0.9, 0.1, 0.6, 0.2],  # Visually similar to Air Max 90
    'pegasustrail.jpg': [0.1, 0.7, 0.2, 0.3],  # A bit like Pegasus
    'jordan1.jpg': [0.5, 0.5, 0.9, 0.8],  # High "basketball" & "high-top" features
    'reactinfinity.jpg': [0.3, 0.8, 0.2, 0.5],  # Also similar to Pegasus/Zoom Fly
    'blazer.jpg': [0.7, 0.3, 0.7, 0.1]  # Similar to Air Max 90
}


def _get_visual_embedding(image_url):
    """
    (Internal Helper) Simulates our custom-trained CBIR model.
    Takes an image URL and returns its feature vector.
    """
    # In a real project:
    # 1. image = load_image_from_url(image_url)
    # 2. preprocessed_image = preprocess(image)
    # 3. vector = cnn_model.predict(preprocessed_image)
    # 4. return vector

    # For our simulation, we just look it up
    return EMBEDDING_REGISTRY.get(image_url, [0, 0, 0, 0])  # Return a zero vector if not found


def _calculate_visual_similarity(seed_embedding, candidate_embedding):
    """(Internal Helper) Calculates cosine similarity."""
    seed_vector = np.array(seed_embedding).reshape(1, -1)
    candidate_vector = np.array(candidate_embedding).reshape(1, -1)
    # [0][0] extracts the single float value from the 2D array result
    return cosine_similarity(seed_vector, candidate_vector)[0][0]


def get_visual_recommendations(seed_shoe, top_20_df, top_n=5):
    """
    STAGE 2: Re-ranks the provided list of shoes based on
    visual similarity to the seed shoe.
    """
    print("[visual_recommender]: Starting Stage 2 re-rank...")

    # Get the seed shoe's visual vector once
    seed_embedding = _get_visual_embedding(seed_shoe['image_url'])

    # Calculate the visual similarity score for *only* the top 20 shoes
    scores = top_20_df.apply(
        lambda row: _calculate_visual_similarity(
            seed_embedding,
            _get_visual_embedding(row['image_url'])
        ),
        axis=1
    )

    # Add the new scores to the DataFrame
    recommendations_df = top_20_df.copy()
    recommendations_df['visual_similarity_score'] = scores

    # Sort by the new visual score and return the top N
    final_recommendations = recommendations_df.sort_values(
        by='visual_similarity_score', ascending=False
    ).head(top_n)

    print(f"[visual_recommender]: Re-ranked and returning top {len(final_recommendations)}.")
    return final_recommendations