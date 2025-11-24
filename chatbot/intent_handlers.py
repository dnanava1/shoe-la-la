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
import textwrap
from recommender.app import run_app

# Instantiate once
watchlist_mgr = WatchlistManager()


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
# def handle_add_watchlist(intent_json):
#     """Adds a shoe (unique_size_id) to a user's watchlist."""

#     user_id = intent_json.get("user_id", "user_001")
#     shoe_name = intent_json.get("shoe_name")
#     constraints = intent_json.get("constraints", {})

#     color = constraints.get("shoe_color")
#     size = constraints.get("shoe_size")

#     # First, get the shoe details to show what we're adding
#     result = handle_view_details_query(intent_json)

#     final_recommendations = run_app(shoe_name)

#     if not result:
#         return "❌ Couldn't find that shoe to add to watchlist. Please check the details."

#     name, actual_color, size_label, price, original, discount, url, image_url = result

#     # Convert shoe → variant → size_id
#     unique_size_id = find_unique_size_id(shoe_name, "", actual_color, str(size))

#     if not unique_size_id:
#         return "❌ Couldn't identify the exact size variant to watch."

#     watchlist_id = watchlist_mgr.add_to_watchlist(user_id, unique_size_id)

#     if not watchlist_id:
#         # Already in watchlist - show current details with image
#         md = f"""
# ### ✅ Already in Watchlist

# **{name}** is already in your watchlist!

# """
#         if image_url:
#             md += f"![{name}]({image_url})\n\n"

#         md += f"""
# **Current Details:**
# - 🎨 Color: {actual_color}
# - 📏 Size: {size_label}
# - 💰 Price: ${price}
# - 🏷️ Original: ${original}
# - 🎯 Discount: {discount}%

# [🔗 View Product]({url})

# ---
# I'll keep monitoring this item for price changes! 📈
# """
#     else:
#         # Successfully added - show confirmation with image and details
#         md = f"""
# ### ✅ Added to Watchlist!

# **{name}** has been added to your watchlist.

# """
#         if image_url:
#             md += f"![{name}]({image_url})\n\n"

#         md += f"""
# **Item Details:**
# - 🎨 Color: {actual_color}
# - 📏 Size: {size_label}
# - 💰 Current Price: ${price}
# - 🏷️ Original Price: ${original}
# - 🎯 Discount: {discount}%

# [🔗 View Product]({url})

# ---
# 📊 **I'll monitor this item** and notify you of any price changes!
# **Watchlist ID**: {watchlist_id}
# """

#     return textwrap.dedent(md).strip()

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

    # Build markdown response
    if watchlist_id:
        md = f"### ✅ Added **{name}** to your watchlist!\n\n"
    else:
        md = f"### ⚠️ **{name}** is already in your watchlist.\n\n"

    if image_url:
        md += f"![{name}]({image_url})\n\n"

    md += f"""
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
        md += f"**Watchlist ID**: {watchlist_id}\n\n"

    # Add final_recommendations (if not empty)
    if final_recommendations is not None and not final_recommendations.empty:
        md += "### 💡 You might also like these shoes:\n"
        for idx, row in final_recommendations.iterrows():
            rec_name = row.get("name")
            rec_price = row.get("price")
            rec_category = row.get("category")
            rec_url = row.get("url", "#")  # optional, if available
            md += f"- **{rec_name}** ({rec_category}) - ${rec_price} [🔗]({rec_url})\n"

    return textwrap.dedent(md).strip()



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