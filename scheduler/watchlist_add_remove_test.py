from scheduler.watchlist_manager import WatchlistManager

wm = WatchlistManager()

# Example values — use your actual ones
user_id = "user_002"
unique_size_id = "PROD-27DB0880_BIG_KIDS_FZ6734-001_1.5Y"

new_watch_id = wm.add_to_watchlist(user_id, unique_size_id)
print(f"✅ Added item to watchlist: {new_watch_id}")

# removed = wm.remove_from_watchlist("watch_003")
# print(f"✅ Removed: {removed}")