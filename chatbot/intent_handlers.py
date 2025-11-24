# intent_handlers.py
"""
Intent Handlers for Chatbot
Handles:
- view_details
- add_to_watchlist
- remove_from_watchlist
"""

from database.queries import find_unique_size_id, handle_view_details_query, get_shoe_details_by_size_id
from scheduler.watchlist_manager import WatchlistManager
from database.queries import get_shoe_details_by_color_id
import textwrap
from recommender.app import run_app

# Instantiate once
watchlist_mgr = WatchlistManager()


def get_recommendation_details_by_id(shoe_id):
    """Get complete shoe details for recommendations using unique_size_id"""
    return get_shoe_details_by_size_id(shoe_id)


# ---------------------------------------------------------
# 1. VIEW DETAILS - WITH IMAGE
# ---------------------------------------------------------
def handle_view_details(intent_json):
    from database.queries import handle_view_details_query
    result = handle_view_details_query(intent_json)

    if not result:
        return "❌ Couldn't find that shoe. Try giving more details!"

    # Now we get 8 values including image URL
    name, color, size_label, price, original, discount, url, image_url = result

    md = f"""
### 👟 **{name}**

"""

    # Add image if available
    if image_url:
        md += f"![{name}]({image_url})\n\n"

    md += f"""
| Detail | Information |
|--------|-------------|
| 🎨 **Color** | {color} |
| 📏 **Size** | {size_label} |
| 💰 **Current Price** | **${price}** |
| 🏷️ **Original Price** | ${original} |
| 🎯 **Discount** | {discount}% off |

💡 **You save**: **${float(original) - float(price):.2f}**!

[🔗 View Product on Nike.com]({url})

---
*Want to track this item? Say "Add this to my watchlist"!*
"""

    return textwrap.dedent(md).strip()

# ---------------------------------------------------------
# 2. ADD TO WATCHLIST - WITH IMAGE AND DETAILS
# ---------------------------------------------------------

def handle_add_watchlist(intent_json):
    """Adds a shoe (unique_size_id) to a user's watchlist and shows recommendations."""

    user_id = intent_json.get("user_id", "user_001")
    shoe_name = intent_json.get("shoe_name")
    constraints = intent_json.get("constraints", {})

    color = constraints.get("shoe_color")
    size = constraints.get("shoe_size")

    # First, get the shoe details to show what we're adding
    result = handle_view_details_query(intent_json)

    # Run recommendation engine
    final_recommendations = run_app(shoe_name)  # returns a DataFrame

    if not result:
        return "❌ Couldn't find that shoe to add to watchlist. Please check the details."

    name, actual_color, size_label, price, original, discount, url, image_url = result

    # Convert shoe → variant → size_id
    unique_size_id = find_unique_size_id(shoe_name, "", actual_color, str(size))
    watchlist_id = watchlist_mgr.add_to_watchlist(user_id, unique_size_id)

    # Build main response
    if watchlist_id:
        response = f"### ✅ Added **{name}** to your watchlist!\n\n"
    else:
        response = f"### ⚠️ **{name}** is already in your watchlist.\n\n"

    if image_url:
        response += f"![{name}]({image_url})\n\n"

    response += f"""
**Details:**
- 🎨 Color: {actual_color}
- 📏 Size: {size_label}
- 💰 Current Price: ${price}
- 🏷️ Original Price: ${original}
- 🎯 Discount: {discount}%

[🔗 View Product]({url})

---
"""

    if watchlist_id:
        response += f"**Watchlist ID**: {watchlist_id}\n\n"

    # Add recommendations using unique_color_id
    if final_recommendations is not None and not final_recommendations.empty:
        response += "### 💡 You might also like these shoes:\n\n"

        for idx, row in final_recommendations.iterrows():
            unique_color_id = row.get("shoe_id")  # This is actually unique_color_id
            rec_name = row.get("name", "Unknown Shoe")

            print(f"🔍 [DEBUG] Processing: {rec_name}, unique_color_id: {unique_color_id}")

            # Get complete details using unique_color_id
            rec_details = None
            if unique_color_id:
                rec_details = get_shoe_details_by_color_id(unique_color_id)
                print(f"🔍 [DEBUG] get_shoe_details_by_color_id result: {rec_details}")

            if rec_details is not None:
                print("🔍 [DEBUG] rec_details fetched successfully")
                # Use the complete details from the database
                rec_image_url = rec_details.get('image_url')
                rec_url = rec_details.get('color_url')
                rec_price = rec_details.get('price')
                rec_original = rec_details.get('original_price')
                rec_discount = rec_details.get('discount_percent')
                rec_color = rec_details.get('color')
                rec_size_label = rec_details.get('size_label')

                print(f"🔍 [DEBUG] Image URL: {rec_image_url}")
                print(f"🔍 [DEBUG] Product URL: {rec_url}")
            else:
                print(f"🔍 [DEBUG] No details found for unique_color_id: {unique_color_id}")
                # Fallback: try to get details by shoe name
                rec_details = get_recommendation_details_by_name(rec_name)
                if rec_details:
                    rec_image_url = rec_details.get('image_url')
                    rec_url = rec_details.get('color_url')
                    rec_price = rec_details.get('price')
                    rec_original = rec_details.get('original_price')
                    rec_discount = rec_details.get('discount_percent')
                    rec_color = rec_details.get('color')
                    rec_size_label = rec_details.get('size_label')
                else:
                    # Final fallback to basic data from recommendations
                    rec_image_url = None
                    rec_url = row.get("color_url", "#")
                    rec_price = row.get("price", "N/A")
                    rec_original = row.get("original_price", rec_price)
                    rec_discount = row.get("discount_percent", 0)
                    rec_color = row.get("colors", ["Unknown Color"])[0] if isinstance(row.get("colors"), list) and row.get("colors") else "Unknown Color"
                    rec_size_label = "Various Sizes"

            # Build recommendation in the same format as view_details
            rec_response = f"### 👟 **{rec_name}**\n\n"

            if rec_image_url and rec_image_url != "" and rec_image_url != "#":
                rec_response += f"![{rec_name}]({rec_image_url})\n\n"
            else:
                # Use default image if no image URL available
                default_image = "https://static.nike.com/a/images/t_PDP_1728_v1/f_auto,q_auto:eco/b7d9211c-26e7-431a-ac24-b0540fb3c00f/air-force-1-07-mens-shoes-jBrhbr.png"
                rec_response += f"![{rec_name}]({default_image})\n\n"

            rec_response += f"""
| Detail | Information |
|--------|-------------|
| 🎨 **Color** | {rec_color} |
| 📏 **Size** | {rec_size_label} |
| 💰 **Current Price** | **${rec_price}** |
| 🏷️ **Original Price** | ${rec_original} |
| 🎯 **Discount** | {rec_discount}% off |

💡 **You save**: **${float(rec_original) - float(rec_price):.2f}**!

"""

            # Only show View Product link if we have a valid URL
            if rec_url and rec_url != "#" and rec_url != "":
                rec_response += f"[🔗 View Product on Nike.com]({rec_url})"
            else:
                rec_response += "🔗 Product link not available"

            rec_response += "\n\n---\n"
            response += rec_response

    return response

# ---------------------------------------------------------
# 3. REMOVE FROM WATCHLIST
# ---------------------------------------------------------
def handle_remove_watchlist(intent_json):
    """Removes a watchlist entry."""

    watchlist_id = intent_json.get("watchlist_id")

    if not watchlist_id:
        return "❌ Missing watchlist_id to remove."

    success = watchlist_mgr.remove_from_watchlist(watchlist_id)

    if not success:
        return "❌ Could not remove that item. Please check the ID."

    return f"🗑️ Removed **{watchlist_id}** from your watchlist."


# ---------------------------------------------------------
# Explicit export list (avoids accidental imports)
# ---------------------------------------------------------
__all__ = [
    "handle_view_details",
    "handle_add_watchlist",
    "handle_remove_watchlist",
]