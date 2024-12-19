import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import threading
import re
from datetime import datetime, timedelta

# Load data from the latest SkiPrices.csv
def load_data():
    files = os.listdir()
    pattern = re.compile(r"prices_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\.csv")
    latest_file = None
    latest_time = None

    for file in files:
        match = pattern.match(file)
        if match:
            date_part, time_part = match.groups()
            file_datetime = datetime.strptime(f"{date_part}_{time_part}", "%Y-%m-%d_%H-%M-%S")
            if not latest_time or file_datetime > latest_time:
                latest_time = file_datetime
                latest_file = file

    if latest_file:
        try:
            df = pd.read_csv(latest_file)
            if 'Resort Name' in df.columns and 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df["Price (€)"] = pd.to_numeric(df["Price (€)"], errors="coerce")
                return df.sort_values(by=['Resort Name', 'Date'])
        except Exception as e:
            print(f"Error reading file {latest_file}: {e}")

    return pd.DataFrame()

# Display filtered or all data
def display_data():
    for widget in main_frame.winfo_children():
        widget.destroy()

    resort_names = [
        "La Plagne 2100", "Val Thorens", "Les Arcs Panorama", "Tignes", "Valmorel",
        "Val d'Isère", "La Rosière", "Alpe d'Huez", "Grand Massif", "Peisey-Vallandry",
        "Serre Chevalier", "Pragelato Sestriere", "Saint-Moritz"
    ]

    if resort_data.empty:
        tk.Label(main_frame, text="No data available. Hit 'Scrape Data' to fetch data.",
                 font=("Helvetica", 14), bg="#f5f5f5", fg="#333").pack(pady=20)
        return

    # Fixed size for each table frame
    table_width = 270
    table_height = 220
    rows, cols = 3, 4  # Grid configuration: 3 rows, 4 columns

    style = ttk.Style()
    style.configure("Treeview", font=("Helvetica", 12), rowheight=25)
    style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"), background="#007BFF", foreground="black")

    # Adjust row and column weights to center content
    for r in range(rows):
        main_frame.grid_rowconfigure(r, weight=1)
    for c in range(cols):
        main_frame.grid_columnconfigure(c, weight=1)

    # Function to sort table
    def sort_table(table, col, resort_df, reverse):
        sorted_df = resort_df.sort_values(by=col, ascending=not reverse)
        table.delete(*table.get_children())  # Clear table
        for _, row in sorted_df.iterrows():  # Re-insert sorted data
            table.insert("", "end", values=(row["Date"].date(), row["Price (€)"]))
        table.heading(col, command=lambda: sort_table(table, col, resort_df, not reverse))

    for index, resort in enumerate(resort_names):
        row, col = divmod(index, cols)

        # Centered Frame with fixed size
        frame = tk.Frame(main_frame, bg="#EAF4FC", bd=2, relief="ridge", width=table_width, height=table_height)
        frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        frame.grid_propagate(False)

        # Bubbly Resort Title
        tk.Label(frame, text=resort, bg="#007BFF", fg="white", font=("Helvetica", 14, "bold"), pady=5).pack(fill="x")

        # Resort-specific data
        resort_df = resort_data[resort_data['Resort Name'] == resort]

        # Table inside the fixed frame
        table = ttk.Treeview(frame, columns=("Date", "Price (€)"), show="headings", height=8)
        table.heading("Date", text="Date", command=lambda t=table, r=resort_df: sort_table(t, "Date", r, False))
        table.heading("Price (€)", text="Price (€)", command=lambda t=table, r=resort_df: sort_table(t, "Price (€)", r, False))
        table.column("Date", anchor="center", stretch=True, minwidth=120)
        table.column("Price (€)", anchor="center", stretch=True, minwidth=120)
        table.pack(fill="both", expand=True)

        for _, row in resort_df.iterrows():
            table.insert("", "end", values=(row["Date"].date(), row["Price (€)"]))

# Scraper logic
def scrape_data():
    latest_time = get_latest_scrape_time()
    current_time = datetime.now()

    if latest_time and (current_time - latest_time) < timedelta(minutes=30):
        response = messagebox.askyesno("Recent Scrape Detected",
                                       "You have already scraped data within the last 30 minutes.\nAre you sure you want to scrape again?")
        if not response:
            return

    def run_scraper():
        messagebox.showinfo("Info", "Scraping data... Please wait!")
        os.system("python scraper.py")
        global resort_data
        resort_data = load_data()
        display_data()
        messagebox.showinfo("Success", "Data updated successfully!")

    threading.Thread(target=run_scraper).start()

def get_latest_scrape_time():
    files = os.listdir()
    pattern = re.compile(r"prices_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\.csv")
    latest_time = None

    for file in files:
        match = pattern.match(file)
        if match:
            date_part, time_part = match.groups()
            file_datetime = datetime.strptime(f"{date_part}_{time_part}", "%Y-%m-%d_%H-%M-%S")
            if not latest_time or file_datetime > latest_time:
                latest_time = file_datetime
    return latest_time

# Price Filter
def filter_data():
    global resort_data
    filtered_data = load_data()
    min_val, max_val = min_price.get(), max_price.get()

    if not filtered_data.empty:
        filtered_data = filtered_data[
            (filtered_data["Price (€)"] >= min_val) & (filtered_data["Price (€)"] <= max_val)
        ]
        resort_data = filtered_data
        display_data()

# GUI setup
root = tk.Tk()
root.title("Club Med Price Comparison")
root.geometry("1200x600")
root.configure(bg="#f5f5f5")

# Title
tk.Label(root, text="Club Med Price Comparison", font=("Helvetica", 20, "bold"), bg="#f5f5f5", fg="#333").pack(pady=10)

# Buttons
button_frame = tk.Frame(root, bg="#f5f5f5")
button_frame.pack()
ttk.Button(button_frame, text="Scrape Data", command=scrape_data).pack(side="left", padx=10)
ttk.Button(button_frame, text="Refresh", command=display_data).pack(side="left", padx=10)

# Price Range Filter
price_frame = tk.Frame(root, bg="#f5f5f5")
price_frame.pack(pady=10)

tk.Label(price_frame, text="Select Price Range (€):", font=("Helvetica", 12), bg="#f5f5f5", fg="#333").grid(row=0, column=0, columnspan=2, pady=5)

# Slider Values
min_price = tk.IntVar(value=0)
max_price = tk.IntVar(value=5000)

# Real-Time Slider Labels
min_price_label = tk.Label(price_frame, text=f"Min: {min_price.get()} €", font=("Helvetica", 10), bg="#f5f5f5")
min_price_label.grid(row=1, column=2, padx=5)
max_price_label = tk.Label(price_frame, text=f"Max: {max_price.get()} €", font=("Helvetica", 10), bg="#f5f5f5")
max_price_label.grid(row=2, column=2, padx=5)

# Slider Update Functions
def update_min_price(val):
    min_price_label.config(text=f"Min: {int(float(val))} €")

def update_max_price(val):
    max_price_label.config(text=f"Max: {int(float(val))} €")

# Min Slider
tk.Label(price_frame, text="Min:", font=("Helvetica", 10), bg="#f5f5f5").grid(row=1, column=0, padx=5)
min_slider = ttk.Scale(price_frame, from_=0, to=5000, orient="horizontal", variable=min_price, length=300, command=update_min_price)
min_slider.grid(row=1, column=1, padx=5)

# Max Slider
tk.Label(price_frame, text="Max:", font=("Helvetica", 10), bg="#f5f5f5").grid(row=2, column=0, padx=5)
max_slider = ttk.Scale(price_frame, from_=0, to=5000, orient="horizontal", variable=max_price, length=300, command=update_max_price)
max_slider.grid(row=2, column=1, padx=5)

ttk.Button(price_frame, text="Apply Filter", command=filter_data).grid(row=3, column=0, columnspan=2, pady=10)

# Main Frame
main_frame = tk.Frame(root, bg="#f5f5f5")
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Initial Data Load
resort_data = load_data()
display_data()

root.mainloop()
