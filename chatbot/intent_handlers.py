# intent_handlers.py
"""
Intent Handlers for Chatbot
Handles:
- view_details
- add_to_watchlist
- remove_from_watchlist
"""

from database.queries import find_unique_size_id, handle_view_details_query
from scheduler.watchlist_manager import WatchlistManager
import textwrap

# Instantiate once
watchlist_mgr = WatchlistManager()


# ---------------------------------------------------------
# 1. VIEW DETAILS
# ---------------------------------------------------------
def handle_view_details(intent_json):
    from database.queries import handle_view_details_query
    result = handle_view_details_query(intent_json)

    if not result:
        return "❌ Couldn't find that shoe. Try giving more details!"

    name, color, size_label, price, original, discount, url = result

    md = f"""
### **{name}**

🎨 **Color:** {color}
📏 **Size:** {size_label}
💰 **Price:** ${price}
🏷️ **Original:** ${original}
🎯 **Discount:** {discount}%

[🔗 View Product]({url})
"""

    return textwrap.dedent(md).strip()

# ---------------------------------------------------------
# 2. ADD TO WATCHLIST
# ---------------------------------------------------------
def handle_add_watchlist(intent_json):
    """Adds a shoe (unique_size_id) to a user's watchlist."""

    user_id = intent_json.get("user_id", "user_001")  # temporary default
    shoe_name = intent_json.get("shoe_name")
    constraints = intent_json.get("constraints", {})

    color = constraints.get("shoe_color")
    size = constraints.get("shoe_size")

    # Convert shoe → variant → size_id
    unique_size_id = find_unique_size_id(shoe_name, "", color, str(size))

    if not unique_size_id:
        return "❌ Couldn't identify the exact size variant to watch."

    watchlist_id = watchlist_mgr.add_to_watchlist(user_id, unique_size_id)

    if not watchlist_id:
        return "⚠️ This shoe-size is already in your watchlist."

    return f"✅ Added **{shoe_name} – {color}, size {size}** to your watchlist!"


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
