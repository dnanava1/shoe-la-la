# # visualizer.py
# import io
# import requests
# # import tkinter as tk
# # from tkinter import ttk
# from PIL import Image, ImageTk
#
#
# def fetch_image_from_url(url, size=(160, 160)):
#     """Fetch image from URL and return a Tkinter-compatible PhotoImage."""
#     try:
#         response = requests.get(url, timeout=5)
#         response.raise_for_status()
#         img = Image.open(io.BytesIO(response.content))
#         img = img.resize(size, Image.Resampling.LANCZOS)
#         return ImageTk.PhotoImage(img)
#     except Exception:
#         # fallback placeholder
#         placeholder = Image.new("RGB", size, color=(220, 220, 220))
#         return ImageTk.PhotoImage(placeholder)
#
#
# def show_recommendations(seed_shoe, recommendations):
#     """Display the seed shoe and its recommendations in a Tkinter window."""
#     root = tk.Tk()
#     root.title("Clickless AI - Shoe Recommendations")
#     root.geometry("1100x700")
#     root.configure(bg="white")
#
#     # --- SEED SHOE FRAME ---
#     seed_frame = ttk.LabelFrame(root, text="You Liked", padding=10)
#     seed_frame.pack(fill="x", padx=20, pady=10)
#
#     seed_img = fetch_image_from_url(seed_shoe.get("image_url"))
#     seed_label = tk.Label(seed_frame, image=seed_img)
#     seed_label.image = seed_img
#     seed_label.pack(side="left", padx=10)
#
#     seed_info = f"Name: {seed_shoe['name']}\nCategory: {seed_shoe['category']}\nPrice: ${seed_shoe['price']:.2f}"
#     tk.Label(seed_frame, text=seed_info, font=("Helvetica", 12), justify="left").pack(side="left", padx=10)
#
#     # --- RECOMMENDATIONS FRAME ---
#     rec_frame = ttk.LabelFrame(root, text="You Might Also Like", padding=10)
#     rec_frame.pack(fill="both", expand=True, padx=20, pady=10)
#
#     canvas = tk.Canvas(rec_frame, bg="white")
#     scrollbar = ttk.Scrollbar(rec_frame, orient="vertical", command=canvas.yview)
#     scrollable_frame = ttk.Frame(canvas)
#
#     scrollable_frame.bind(
#         "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
#     )
#     canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
#     canvas.configure(yscrollcommand=scrollbar.set)
#
#     canvas.pack(side="left", fill="both", expand=True)
#     scrollbar.pack(side="right", fill="y")
#
#     # --- Populate recommendations ---
#     for _, row in recommendations.iterrows():
#         frame = ttk.Frame(scrollable_frame, padding=8)
#         frame.pack(fill="x", pady=4)
#
#         img = fetch_image_from_url(row.get("image_url"))
#         lbl_img = tk.Label(frame, image=img)
#         lbl_img.image = img
#         lbl_img.pack(side="left")
#
#         info = (
#             f"Name: {row['name']}\n"
#             f"Category: {row['category']}\n"
#             f"Price: ${row['price']:.2f}\n"
#             f"Similarity Score: {row.get('data_similarity_score', 0):.2f}"
#         )
#         tk.Label(frame, text=info, font=("Helvetica", 11), justify="left").pack(side="left", padx=15)
#
#     root.mainloop()
