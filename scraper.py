import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def scrape_clubmed_data():
    PATH = "C:\\Program Files (x86)\\chromedriver.exe"
    service = Service(PATH)
    driver = webdriver.Chrome(service=service)

    # Month mapping
    MONTHS_DICT = {
        "ינו": 1, "פבר": 2, "מרץ": 3, "אפר": 4, "מאי": 5,
        "יוני": 6, "יולי": 7, "אוג": 8, "ספט": 9, "אוק": 10,
        "נוב": 11, "דצמ": 12
    }

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
            time.sleep(3)
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "flex.items-center.px-20.py-12.text-middleGrey"))
            ).click()
            print(f"Clicked 'When' button for {resort['name']}.")
            time.sleep(3)

            # Scrape months from December to April
            while True:
                # Re-fetch month and year
                month_year_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span[id^='react-day-picker']"))
                )
                month_text, year_text = month_year_element.text.split()
                current_page_month = MONTHS_DICT.get(month_text, None)
                current_page_year = int(year_text)

                print(f"Scraping {month_text} {year_text} for {resort['name']}...")

                # Stop if month is after April
                if current_page_month and current_page_month > 4 and current_page_year == datetime.now().year + 1:
                    break

                # Scrape data
                dates = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".rdp-cell button:not([disabled])"))
                )

                if not dates:
                    print(f"No dates available for {month_text} {year_text}. Skipping month.")
                else:
                    for date_element in dates:
                        try:
                            date = date_element.find_element(By.TAG_NAME, "time").get_attribute("datetime")
                            price_element = date_element.find_elements(By.CLASS_NAME, "text-b5")
                            if price_element:
                                price = price_element[0].text.strip().replace("€", "").replace(",", "")
                                if price:
                                    all_data.append({
                                        "Resort Name": resort["name"],
                                        "Date": date,
                                        "Price (€)": price,
                                        "Month-Year": f"{month_text} {year_text}",
                                        "Scraped Date": datetime.today().strftime("%Y-%m-%d"),
                                    })
                                    print(f"Scraped: {date} - {price} €")
                        except Exception as e:
                            print(f"Skipping date due to error: {e}")

                # Navigate to the next month
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR,
                        "button[aria-label='Next-Custom']"
                    ))
                )
                next_button.click()
                time.sleep(3)  # Allow time for the next month to fully load

        except Exception as e:
            print(f"Error for {resort['name']}: {e}")

    # Save data to CSV
    if all_data:
        df = pd.DataFrame(all_data)
        file_name = f"prices_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        df.to_csv(file_name, index=False)
        print(f"Data saved to {file_name}")
    else:
        print("No valid data was scraped.")

    driver.quit()
