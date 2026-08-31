import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from urllib.parse import urlparse


pd.set_option("display.width", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)


def extract_country(url):
    """
    Extracts and formats the country name from a timeanddate.com weather URL.
    Example: 'https://.../weather/germany/frankfurt' -> 'Germany'
    """
    try:
        path = urlparse(url).path
        path_parts = path.strip("/").split("/")
        
        # Ensure the URL path has at least two parts (e.g., 'weather' and 'country')
        if len(path_parts) >= 2:
            raw_country = path_parts[1].lower()
            
            # Map specific acronyms to their correct capitalization
            acronyms = {
                "usa": "USA",
                "uk": "UK",
                "uae": "UAE"
            }
            
            if raw_country in acronyms:
                return acronyms[raw_country]
                
            # For standard names: replace dashes with spaces and capitalize
            # e.g., "new-zealand" -> "New Zealand"
            return raw_country.replace("-", " ").title()
            
        return "Unknown"
        
    except Exception:
        # Catch any unexpected parsing errors to prevent crashing
        return "Unknown"


MAIN_PAGE_URL = "https://www.timeanddate.com/weather/"

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 10)

city_links = []
all_weather_records = []
months = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]


try:
    driver.get(MAIN_PAGE_URL)

    # Wait until the target table is present in the DOM
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.zebra.fw.tb-theme tbody")))
    # anchor_elements = driver.find_elements(
    #     By.CSS_SELECTOR, "table.zebra.fw.tb-theme tbody tr td a"
    # )
    print("Extracting links via JavaScript to prevent stale elements...")
    extracted_data = driver.execute_script("""
        return Array.from(document.querySelectorAll('table.zebra.fw.tb-theme tbody tr td a'))
             .map(a => [a.innerText.trim(), a.href]);
    """)

    print(f"Found {len(extracted_data)} elements.")

    for city_name, city_url in extracted_data:
        if city_name and city_url:
            city_links.append((city_name, f"{city_url}/climate"))

    for city, url in city_links:
        driver.get(url)

        # Grab the text from the element
        header_text = driver.find_element(By.CSS_SELECTOR, "h1.headline-banner__title").text

        # Split exactly at " in " and take the second half
        location_string = header_text.split(" in ", 1)[1]

        # Split by commas and strip spaces
        parts = [p.strip() for p in location_string.split(',')]

        # Unpack based on whether the region exists (3 parts) or not (2 parts)
        if len(parts) == 3:
            city, region, country = parts[0], parts[1], parts[2]
        else:
            city, region, country = parts[0], None, parts[1]

        # Wait until the target table is present in the DOM
        wait.until(EC.presence_of_element_located((By.ID, "climateTable")))

        for month in months:
            month_class = f"climate-month--{month}"

            try:
                # Locate the specific container for that month
                month_block = driver.find_element(By.CSS_SELECTOR, f"div.climate-month.{month_class}")

                # Get all the <p> tags within this month's block
                p_elements = month_block.find_elements(By.TAG_NAME, "p")

                # Start dictionaty for this specific month
                record = {
                    "city": city,
                    "region": region,
                    "country": country,
                    "month": month.capitalize()
                }

                # Iterate over <p> tags to extract data the key-value pairs
                for p in p_elements:
                    raw_text = p.get_attribute("textContent")

                    if raw_text and ":" in raw_text:
                        # Replace non-breaking spaces with regular spaces
                        text = raw_text.replace('\xa0', ' ')
                        # Split at the first colon to separate key and value
                        key, value = text.split(":", 1)

                        # Clean up the key and value
                        clean_key = key.strip().lower().replace(" ", "_")

                        # Store it in the dictionary
                        record[clean_key] = value.strip()

                # Append the record to the list of all weather records
                all_weather_records.append(record)

                # sleep to avoid overwhelming the server
                time.sleep(1)
            except NoSuchElementException:
                print(f"Could not find data for {month} in {city}.")


finally:
    driver.quit()

# Write data to csv file with UTF-8 encoding
pd.DataFrame(all_weather_records).to_csv("climate_data.csv", index=False, encoding="utf-8-sig")
