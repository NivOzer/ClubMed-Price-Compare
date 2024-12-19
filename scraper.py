import pandas as pd
import time  # Import time for delays
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def scrape_clubmed_data():
    PATH = "C:\Program Files (x86)\chromedriver.exe"  # Update path if necessary
    service = Service(PATH)
    driver = webdriver.Chrome(service=service)

    resort_urls = [
        {"url": "https://www.clubmed.co.il/r/la-plagne-2100/y?departure_city=TLV", "name": "La Plagne 2100"},
        {"url": "https://www.clubmed.co.il/r/val-thorens-sensations/y?departure_city=TLV", "name": "Val Thorens"},
        {"url": "https://www.clubmed.co.il/r/les-arcs-panorama/w?departure_city=TLV", "name": "Les Arcs Panorama"},
        {"url": "https://www.clubmed.co.il/r/tignes/w?departure_city=TLV", "name": "Tignes"},
        {"url": "https://www.clubmed.co.il/r/valmorel/w?departure_city=TLV", "name": "Valmorel"},
        {"url": "https://www.clubmed.co.il/r/val-d-isere/w?departure_city=TLV", "name": "Val d'Isère"},
        {"url": "https://www.clubmed.co.il/r/la-rosiere/w", "name": "La Rosière"},
        {"url": "https://www.clubmed.co.il/r/alpe-d-huez/w?departure_city=TLV", "name": "Alpe d'Huez"},
        {"url": "https://www.clubmed.co.il/r/grand-massif-samoens-morillon/w?departure_city=TLV", "name": "Grand Massif"},
        {"url": "https://www.clubmed.co.il/r/peisey-vallandry/w?departure_city=TLV", "name": "Peisey-Vallandry"},
        {"url": "https://www.clubmed.co.il/r/serre-chevalier/w?departure_city=TLV", "name": "Serre Chevalier"},
        {"url": "https://www.clubmed.co.il/r/pragelato-sestriere/w?departure_city=TLV", "name": "Pragelato Sestriere"},
        {"url": "https://www.clubmed.co.il/r/saint-moritz-roi-soleil/y?departure_city=TLV", "name": "Saint-Moritz"},
    ]

    all_data = []

    for resort in resort_urls:
        try:
            driver.get(resort["url"])
            time.sleep(3)  # Wait for the page to fully load
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "flex.items-center.px-20.py-12.text-middleGrey"))
            ).click()
            print(f"Clicked 'When' button for {resort['name']}.")
            time.sleep(2)  # Allow time for calendar to load

            # Scrape December to April for each resort
            for month_iteration in range(5):
                try:
                    # Re-fetch month-year for each iteration
                    month_year_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span[id^='react-day-picker']"))
                    )
                    month_year = month_year_element.text
                    print(f"Scraping {month_year} for {resort['name']}...")

                    # Re-fetch the dates to avoid stale references
                    dates = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".rdp-cell button:not([disabled])"))
                    )
                    for date_element in dates:
                        try:
                            # Re-fetch time and price to ensure no stale element
                            date = date_element.find_element(By.TAG_NAME, "time").get_attribute("datetime")
                            price_element = date_element.find_elements(By.CLASS_NAME, "text-b5")
                            if price_element:
                                price = price_element[0].text.strip().replace("€", "").replace(",", "")
                                if price:
                                    all_data.append({
                                        "Resort Name": resort["name"],
                                        "Date": date,
                                        "Price (€)": price,
                                        "Month-Year": month_year,
                                        "Scraped Date": datetime.today().strftime("%Y-%m-%d"),
                                    })
                                    print(f"Scraped: {date} - {price} €")
                        except Exception as e:
                            print(f"Skipping date due to stale reference: {e}")

                    # Click "Next" and wait for the next calendar to load
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR,
                            "body > main > div > div.hidden.md\\:block > div > div > div > div.pointer-events-auto.mt-12.w-fit > div > div.relative.h-full.w-full.overflow-y-auto > div > div:nth-child(2) > div > div > div.rdp-month.rdp-caption_end > div > button"
                        ))
                    )
                    next_button.click()
                    time.sleep(2)  # Wait for the next month to fully load
                except Exception as e:
                    print(f"Error during scraping month {month_iteration + 1} for {resort['name']}: {e}")
                    break

        except Exception as e:
            print(f"Error for {resort['name']}: {e}")

    # Save data to CSV
    if all_data:
        df = pd.DataFrame(all_data)
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"prices_{current_time}.csv"
        df.to_csv(file_name, index=False)
        print(f"Data saved to '{file_name}'")

    else:
        print("No valid data was scraped.")

    driver.quit()

scrape_clubmed_data()
