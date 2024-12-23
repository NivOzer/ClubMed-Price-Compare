import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
import os
import threading
import re
from datetime import datetime, timedelta


def scrape_data():
    def scrape_thread():
        messagebox.showinfo("Scraping", "Scraping data. This may take a while.")
        from scraper import scrape_clubmed_data
        scrape_clubmed_data()
        global resort_data
        resort_data = load_data()
        display_data()
        messagebox.showinfo("Scraping Complete", "Data scraping complete.")

    threading.Thread(target=scrape_thread, daemon=True).start()

def load_data():
    files = os.listdir()
    pattern = re.compile(r"prices_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\.csv")
    latest_file = None
    latest_time = None

    for file in files:
        match = pattern.match(file)
        if match:
            date_part, time_part = match.groups()  # Extract date_part and time_part here
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
                return df.drop_duplicates().sort_values(by=['Resort Name', 'Date'])
        except Exception as e:
            print(f"Error reading file {latest_file}: {e}")

    return pd.DataFrame()


def display_data(data=None):
    for widget in main_frame.winfo_children():
        widget.destroy()

    resort_names = [
        "La Plagne 2100", "Val Thorens", "Les Arcs Panorama", "Tignes", "Valmorel",
        "Val d'Isère", "La Rosière", "Alpe d'Huez", "Grand Massif", "Peisey-Vallandry",
        "Serre Chevalier", "Pragelato Sestriere", "Saint-Moritz"
    ]

    current_data = data if data is not None else resort_data

    if current_data.empty:
        tk.Label(main_frame, text="No data available. Hit 'Scrape Data' to fetch data.",
                 font=("Helvetica", 14), bg="#f5f5f5", fg="#333").pack(pady=20)
        return

    rows, cols = 3, 4

    style = ttk.Style()
    style.configure("Treeview", font=("Helvetica", 12), rowheight=25)
    style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"), background="#007BFF", foreground="black")

    for r in range(rows):
        main_frame.grid_rowconfigure(r, weight=1)
    for c in range(cols):
        main_frame.grid_columnconfigure(c, weight=1)

    def sort_table(table, col, resort_df, reverse):
        sorted_df = resort_df.sort_values(by=col, ascending=not reverse)
        table.delete(*table.get_children())
        for _, row in sorted_df.iterrows():
            table.insert("", "end", values=(row["Date"].date(), row["Price (€)"]))
        table.heading(col, command=lambda: sort_table(table, col, resort_df, not reverse))

    for index, resort in enumerate(resort_names):
        row, col = divmod(index, cols)

        frame = ttk.Frame(main_frame)
        frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        frame.grid_propagate(False)

        ttk.Label(frame, text=resort, background="#007BFF", foreground="white", font=("Helvetica", 14, "bold"), anchor="center").pack(fill="x")

        resort_df = (
            current_data[current_data['Resort Name'] == resort]
            .drop_duplicates(subset=['Date'], keep='first')
        )

        table = ttk.Treeview(frame, columns=("Date", "Price (€)"), show="headings", height=8)
        table.heading("Date", text="Date", command=lambda t=table, r=resort_df: sort_table(t, "Date", r, False))
        table.heading("Price (€)", text="Price (€)", command=lambda t=table, r=resort_df: sort_table(t, "Price (€)", r, False))
        table.column("Date", anchor="center", stretch=True, minwidth=120)
        table.column("Price (€)", anchor="center", stretch=True, minwidth=120)
        table.pack(fill="both", expand=True)

        for _, row in resort_df.iterrows():
            table.insert("", "end", values=(row["Date"].date(), row["Price (€)"]))

def filter_data():
    global resort_data
    start_date = pd.Timestamp(start_date_var.get_date())
    end_date = pd.Timestamp(end_date_var.get_date())
    print(start_date)
    print(end_date)
    max_val = price_range_var.get()

    if start_date and end_date:
        filtered_data = resort_data[(resort_data["Date"] >= start_date) &
                                    (resort_data["Date"] <= end_date) &
                                    (resort_data["Price (€)"] <= max_val)]
        if not filtered_data.empty:
            display_data(filtered_data)
        else:
            messagebox.showinfo("No Data", "No data available for the selected filters.")
    else:
        messagebox.showerror("Invalid Filters", "Please select a valid date range and price range.")

root = tk.Tk()
root.title("Club Med Price Comparison")
root.geometry("1200x700")
root.configure(bg="#f5f5f5")

ttk.Label(root, text="Club Med Price Comparison", font=("Helvetica", 20, "bold"), background="#f5f5f5", foreground="#333").pack(pady=10)

filter_frame = ttk.Frame(root)
filter_frame.pack(pady=10, padx=10, fill="x")

ttk.Button(filter_frame, text="Scrape Data", command=scrape_data).grid(row=3, column=4, pady=10, padx=5, sticky="e")

ttk.Label(filter_frame, text="Start Date:", font=("Helvetica", 12)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
start_date_var = DateEntry(filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
start_date_var.grid(row=0, column=1, padx=5, pady=5, sticky="w")
start_date_var.set_date("01-12-2024")

ttk.Label(filter_frame, text="End Date:", font=("Helvetica", 12)).grid(row=0, column=2, padx=5, pady=5, sticky="w")
end_date_var = DateEntry(filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
end_date_var.grid(row=0, column=3, padx=5, pady=5, sticky="w")
end_date_var.set_date("28-04-2025")

ttk.Label(filter_frame, text="Max Price (€):", font=("Helvetica", 12)).grid(row=1, column=0, padx=5, pady=5, sticky="w")
price_range_var = tk.DoubleVar(value=5000)
price_range = ttk.Scale(filter_frame, from_=0, to=5000, orient="horizontal", length=300, variable=price_range_var)
price_range.grid(row=1, column=1, columnspan=3, padx=5, pady=5)
price_value = tk.Label(filter_frame, text=f"Max: 5000 €", font=("Helvetica", 10))
price_value.grid(row=2, column=1, columnspan=3, padx=5, pady=5)

def update_price_range(val):
    price_value.config(text=f"Max: {int(float(val))} €")

price_range.configure(command=update_price_range)

ttk.Button(filter_frame, text="Apply Filters", command=filter_data).grid(row=3, column=0, columnspan=4, pady=10)

main_frame = ttk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

resort_data = load_data()
display_data()

root.mainloop()
