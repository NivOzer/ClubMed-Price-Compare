import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
import matplotlib.backends.backend_tkagg as tkagg
from tkinter import Tk, Canvas, Scrollbar, Frame
from matplotlib.backend_bases import MouseEvent
from matplotlib.collections import PathCollection

def load_all_data():
    files = os.listdir()
    pattern = re.compile(r"prices_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\.csv")
    all_data = []

    for file in files:
        if pattern.match(file):
            try:
                df = pd.read_csv(file)
                if 'Resort Name' in df.columns and 'Date' in df.columns and 'Scraped Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df['Scraped Date'] = pd.to_datetime(df['Scraped Date'])
                    df["Price (€)"] = pd.to_numeric(df["Price (€)"], errors="coerce")
                    df['File Date'] = file.split('_')[1]  # Extract only the date part of the file name
                    all_data.append(df)
            except Exception as e:
                print(f"Error reading {file}: {e}")

    if all_data:
        combined_data = pd.concat(all_data).drop_duplicates()
        # Ensure duplicates are removed before aggregation
        combined_data = combined_data.sort_values(by=['Date', 'Resort Name', 'Price (€)']).drop_duplicates(subset=['Date', 'Resort Name'])
        return combined_data.sort_values(by=['Date', 'Resort Name'])
    return pd.DataFrame()

def annotate_hover(fig, ax, data):
    scatter = next((obj for obj in ax.collections if isinstance(obj, PathCollection)), None)
    if scatter is None:
        return

    annot = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                        textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="#f0f8ff"),
                        arrowprops=dict(arrowstyle="->", color="#1f77b4"))
    annot.set_visible(False)

    def update_annot(ind):
        pos = scatter.get_offsets()[ind["ind"][0]]
        annot.xy = pos
        row = data.iloc[ind["ind"][0]]  # Correctly reference the row of the hovered point
        date = row['Date']
        price = row['Price (€)']
        file_date = row['File Date']
        days_before = (date - row['Scraped Date']).days
        annot.set_text(f"Date: {date:%Y-%m-%d}\nPrice: €{price:.2f}\nFile Date: {file_date}\nDays Before: {days_before}")
        annot.get_bbox_patch().set_facecolor('#d4ebf2')
        annot.get_bbox_patch().set_alpha(0.9)

    def hover(event: MouseEvent):
        vis = annot.get_visible()
        if event.inaxes == ax:
            cont, ind = scatter.contains(event)
            if cont:
                update_annot(ind)
                annot.set_visible(True)
                fig.canvas.draw_idle()
            else:
                if vis:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)

def highlight_best_prices(ax, data):
    best_prices = data.nsmallest(5, 'Price (€)')
    sns.scatterplot(
        data=best_prices,
        x='Date',
        y='Price (€)',
        color='green',
        s=120,
        label="Top 5 Prices",
        ax=ax
    )

def plot_best_price_dates(data, canvas):
    if data.empty:
        print("No data to visualize.")
        return

    sns.set_theme(style="whitegrid")

    # General Trend for All Resorts
    trend_data = (
        data.groupby(['Date'])['Price (€)']
        .min()
        .reset_index()
        .sort_values(by='Date')
    )

    general_fig, ax = plt.subplots(figsize=(20, 10))
    sns.lineplot(data=trend_data, x='Date', y='Price (€)', label="Price Trend", color='#1f77b4', ax=ax, linewidth=2)
    sns.scatterplot(data=trend_data, x='Date', y='Price (€)', color='#ff7f0e', alpha=0.8, s=80, label="Prices", ax=ax)
    highlight_best_prices(ax, data)
    ax.set_title("Best Prices by Vacation Date (All Resorts)", fontsize=20, color="#1f77b4")
    ax.set_xlabel("Vacation Date", fontsize=14, color="#1f77b4")
    ax.set_ylabel("Price (€)", fontsize=14, color="#1f77b4")
    ax.legend(fontsize=12, loc="upper right")
    ax.grid(True, which="major", color="#cccccc", linestyle="--", linewidth=0.5)

    annotate_hover(general_fig, ax, data)
    tkagg.FigureCanvasTkAgg(general_fig, canvas).get_tk_widget().pack(pady=20)

    # Individual Trends for Each Resort
    resorts = data['Resort Name'].unique()
    for resort in resorts:
        resort_data = data[data['Resort Name'] == resort]
        trend_resort = (
            resort_data.groupby(['Date'])['Price (€)']
            .min()
            .reset_index()
            .sort_values(by='Date')
        )

        resort_fig, ax = plt.subplots(figsize=(20, 5))
        sns.lineplot(data=trend_resort, x='Date', y='Price (€)', label="Price Trend", color='#1f77b4', ax=ax, linewidth=2)
        sns.scatterplot(data=trend_resort, x='Date', y='Price (€)', color='#ff7f0e', alpha=0.8, s=80, label="Prices", ax=ax)
        highlight_best_prices(ax, resort_data)
        ax.set_title(f"Best Prices by Vacation Date: {resort}", fontsize=18, color="#1f77b4")
        ax.set_xlabel("Vacation Date", fontsize=12, color="#1f77b4")
        ax.set_ylabel("Price (€)", fontsize=12, color="#1f77b4")
        ax.legend(fontsize=10, loc="upper right")
        ax.grid(True, which="major", color="#cccccc", linestyle="--", linewidth=0.5)

        annotate_hover(resort_fig, ax, resort_data)
        tkagg.FigureCanvasTkAgg(resort_fig, canvas).get_tk_widget().pack(pady=20)

def main():
    root = Tk()
    root.title("Scrollable Best Price Dates")
    root.geometry("1920x1080")

    # Create a scrollable canvas
    main_frame = Frame(root)
    main_frame.pack(fill="both", expand=True)

    canvas = Canvas(main_frame)
    scrollbar = Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas)

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    data = load_all_data()
    if data.empty:
        print("No data available.")
        return

    print("Data loaded successfully.")
    plot_best_price_dates(data, scrollable_frame)

    root.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1 * (event.delta // 120), "units"))
    root.mainloop()

if __name__ == "__main__":
    main()
