# chatbot_adapter.py
import sys
import os
import pandas as pd

# --- PATH FIX: Ensure we can import from the 'recommender' folder ---
# 1. Get the directory where this file (chatbot_adapter.py) lives
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Go up one level to the project root (SHOE-LA-LA)
project_root = os.path.abspath(os.path.join(current_dir, ".."))

# 3. Define the recommender path
recommender_path = os.path.join(project_root, "recommender")

# 4. Add to system path if not already there
if recommender_path not in sys.path:
    sys.path.append(recommender_path)
# --------------------------------------------------------------------

# Now imports will work successfully
import data_manager
import recommender_engine

# Load data once at startup to keep the chatbot fast
print("[chatbot_adapter]: Loading Shoe Database...")
try:
    ALL_SHOES_DF = data_manager.load_shoe_database()
except Exception as e:
    print(f"[chatbot_adapter]: Error loading database: {e}")
    ALL_SHOES_DF = pd.DataFrame() # Fallback to empty

def handle_search_intent(intent_json):
    """
    Handles 'search' and 'recommend' intents.
    Translates LLM constraints into Recommender criteria and returns Markdown.
    """
    # 1. Check Data Availability
    if ALL_SHOES_DF.empty:
        return "⚠️ **System Error**: Shoe database is empty or could not be loaded. Please check the database connection."

    # 2. Extract & Map Criteria
    # The LLM returns structure like: 
    # {"constraints": {"shoe_color": "red", "price_max": 100}, "shoe_name": "Jordan"}
    
    llm_constraints = intent_json.get("constraints", {})
    shoe_name_query = intent_json.get("shoe_name", "")
    
    # The Recommender expects keys: "color", "max_price", "query", "gender"
    criteria = {}

    # Map 'shoe_name' to 'query'
    if shoe_name_query:
        criteria["query"] = shoe_name_query

    # Map specific constraints
    if "shoe_color" in llm_constraints:
        criteria["color"] = llm_constraints["shoe_color"]
    
    if "shoe_gender" in llm_constraints:
        criteria["gender"] = llm_constraints["shoe_gender"]
        
    if "price_max" in llm_constraints:
        criteria["max_price"] = llm_constraints["price_max"]
        
    if "price_min" in llm_constraints:
        criteria["min_price"] = llm_constraints["price_min"]

    # If no criteria found (empty search)
    if not criteria and not shoe_name_query:
        return "Please specify what kind of shoes you are looking for (e.g., 'Black running shoes' or 'Jordans under $150')."

    # 3. Call Recommender Engine
    # This uses the new filtering logic we added to the engine
    recommendations = recommender_engine.get_recommendations_by_criteria(criteria, ALL_SHOES_DF)

    # 4. Format Output (Markdown)
    if recommendations.empty:
        criteria_str = _format_criteria_string(criteria)
        return f"😕 I couldn't find any shoes matching those criteria ({criteria_str}). Try broadening your search (e.g. remove the price limit)."

    return _format_recommendations_as_markdown(recommendations)


def _format_criteria_string(criteria):
    """Helper to make the error message friendly and readable"""
    parts = []
    if "color" in criteria: parts.append(f"Color: {criteria['color']}")
    if "max_price" in criteria: parts.append(f"Max Price: ${criteria['max_price']}")
    if "query" in criteria: parts.append(f"Keyword: '{criteria['query']}'")
    if "gender" in criteria: parts.append(f"Gender: {criteria['gender']}")
    return ", ".join(parts)


def _format_recommendations_as_markdown(df):
    """
    Creates a Markdown response compatible with Streamlit.
    """
    response = ["### 👟 **Here are my top picks:**\n"]
    
    for i, row in df.iterrows():
        name = row.get('name', 'Unknown Shoe')
        price = row.get('price')
        original_price = row.get('original_price')
        colors = row.get('colors', [])
        
        # Format Color String
        if isinstance(colors, list):
            color_str = ", ".join(colors[:2]) # Just show first 2 colors
        else:
            color_str = "Various"

        url = row.get('base_url', '#')
        img_url = row.get('image_url') or row.get('color_image_url')
        
        # Determine price display (Handle Sales)
        if price and pd.notna(price):
            price_display = f"**${price:.2f}**"
            if original_price and pd.notna(original_price) and original_price > price:
                price_display += f" (~~${original_price:.2f}~~)"
        else:
            price_display = "Price N/A"

        # Construct Markdown Card
        card = f"""
**{i+1}. [{name}]({url})**
- 💰 Price: {price_display}
- 🎨 Color: {color_str}
"""
        # Add image if valid
        if img_url and isinstance(img_url, str) and img_url.startswith("http"):
            card += f"![{name}]({img_url})\n"
        
        response.append(card)
        
    return "\n".join(response)