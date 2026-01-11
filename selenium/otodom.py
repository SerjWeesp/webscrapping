# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""


import time
import os
import math
import pickle
import pandas as pd
import googlemaps
import datetime
today = str(datetime.date.today())
from datetime import datetime
import ctypes

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.edge.service import Service as EdgeService

ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)

SLEEP = 1000
api_key = ''  
edge_driver_path = r'C:\Users\Dell\Downloads\msedgedriver.exe'

# Generate timestamp in ddmmyyyy format
timestamp = datetime.now().strftime('%d%m%Y')
all_links_file = f'all_links_{timestamp}.pkl'
processed_pages_file = f'processed_pages_{timestamp}.pkl'
listings_data_file = f'listings_data_{timestamp}.pkl'

def calculate_travel_time(address, destination_address, key, departure_time=datetime.now()):
    gmaps = googlemaps.Client(key=key)
    try:
        # Calculate travel time by public transport between two destinations
        directions_result = gmaps.directions(address,
                                              destination_address,
                                              mode="transit",
                                              departure_time=departure_time)
        
        # Extract travel time
        if directions_result:
            return directions_result[0]['legs'][0]['duration']['text']
        else:
            return 'No route found'
    except googlemaps.exceptions.ApiError as e:
        # Handle API errors gracefully
        print(f"API Error: {e.status}")
        return 'API Error: Unable to calculate travel time'
    
def parse_num(val):
    if not val:
        return None

    val = (
        val.replace("m²", "")
           .replace("zł", "")
           .replace("\xa0", "")
           .replace(" ", "")
           .replace(",", ".")
           .strip()
    )

    try:
        return float(val)
    except ValueError:
        return None



# Set up Edge WebDriver
options = webdriver.EdgeOptions()
options.add_argument("--blink-settings=imagesEnabled=false")
#options.add_argument("--headless=new")


# Specify the Edge WebDriver executable path
driver = webdriver.Edge(service=EdgeService(edge_driver_path), options=options)

# URL of the website you want to scrape
url = 'https://www.otodom.pl'
# Open the website
driver.get(url)
is_banner_closed = False

# Close Cookies banner
if not is_banner_closed:
    try:
        cookie_banner = driver.find_element(By.ID,'onetrust-accept-btn-handler')
        cookie_banner.click()
        is_banner_closed = True
    except:
        pass

distanceRadius = 0
priceMax=1300000
priceMin=600000
areaMin=50
areaMax=100
buildYearMin = 2025
roomsNumber = '%5BTHREE%2CFOUR%5D'
buildYearMax = 2025

wait = WebDriverWait(driver, 10)

base_url = (
    "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/"
    "mazowieckie/warszawa/warszawa/warszawa"
)

params = (
    f"?distanceRadius={distanceRadius}"
    f"&limit=72"
    f"&ownerTypeSingleSelect=ALL"
    f"&priceMax={priceMax}"
    f"&buildYearMin={buildYearMin}"
    f"&priceMin={priceMin}"
    f"&areaMin={areaMin}"
    f"&areaMax={areaMax}"
    f"&roomsNumber={roomsNumber}"
    f"&buildYearMax={buildYearMax}"
    f"&by=DEFAULT"
    f"&direction=DESC"
    f"&viewType=listing"
    f"&page={{page}}"
)

all_links = set()

# Load existing all_links if available
if os.path.exists(all_links_file):
    with open(all_links_file, 'rb') as f:
        all_links = pickle.load(f)
    print(f"Loaded {len(all_links)} existing links from {all_links_file}")
    start_page = 1  # Will skip already processed pages via pickle tracking
else:
    print("Starting fresh - no existing all_links pickle found")
    start_page = 1

url = base_url + params.format(page=1)
driver.get(url)
try:
    max_pages = math.ceil(int(wait.until(
    EC.presence_of_element_located(
        (By.XPATH, '//*[@id="__next"]/div[2]/main/div/div[2]/div[3]/div[1]/div[1]/div[1]/div/div/div/div[1]/div/div/span')
    )
).text.split()[-1])/72)
except:
    print('No element found. Refreshing')
    time.sleep(SLEEP)
    driver.refresh()
    max_pages = math.ceil(int(wait.until(
    EC.presence_of_element_located(
        (By.XPATH, '//*[@id="__next"]/div[2]/main/div/div[2]/div[3]/div[1]/div[1]/div[1]/div/div/div/div[1]/div/div/span')
    )
).text.split()[-1])/72)

# Track which pages have been processed
if os.path.exists(processed_pages_file):
    with open(processed_pages_file, 'rb') as f:
        processed_pages = pickle.load(f)
    print(f"Resuming from page {max(processed_pages)+2 if processed_pages else 1}/{max_pages}")
else:
    processed_pages = set()

for page in range(1, max_pages + 1):
    if page in processed_pages:
        print(f"Page {page} already processed, skipping...")
        continue
        
    url = base_url + params.format(page=page)
    driver.get(url)

    # Accept cookies once
    if page == 1:
        try:
            wait.until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            ).click()
        except:
            pass

    try: 
    # Wait for listings
       wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'a[data-cy="listing-item-link"]')
            )
        )
    except:
        print('No element found. Refreshing')
        time.sleep(SLEEP)
        driver.refresh()
        wait.until(
             EC.presence_of_all_elements_located(
                 (By.CSS_SELECTOR, 'a[data-cy="listing-item-link"]')
             )
         )

    # Extract links directly via Selenium
    page_links = driver.find_elements(
        By.CSS_SELECTOR, 'a[data-cy="listing-item-link"]'
    )

    for el in page_links:
        href = el.get_attribute("href")
        if href and "undefined" not in href:
            all_links.add(href)
    
    # Save progress after each page
    processed_pages.add(page)
    with open(all_links_file, 'wb') as f:
        pickle.dump(all_links, f)
    with open(processed_pages_file, 'wb') as f:
        pickle.dump(processed_pages, f)
    
    print(f"Page {page}/{max_pages}: Collected {len(all_links)} total links")

print(f"Collected {len(all_links)} links")
if '/hpr/undefined' in all_links:
    all_links.remove('/hpr/undefined')

# Save all_links to pickle file
with open(all_links_file, 'wb') as f:
    pickle.dump(all_links, f)
print(f"Saved all_links to {all_links_file}")

# Load existing listings_data if available
if os.path.exists(listings_data_file):
    with open(listings_data_file, 'rb') as f:
        listings_data = pickle.load(f)
    print(f"Loaded {len(listings_data)} existing listings from {listings_data_file}")
    # Get already processed links
    processed_links = {d['url'].replace('https://www.otodom.pl', '') for d in listings_data}
    remaining_links = all_links - processed_links
    print(f"Resuming from link {len(listings_data)+1}/{len(all_links)}")
else:
    listings_data = []
    remaining_links = all_links
    print("Starting fresh - no existing listings_data pickle found")

for idx, link in enumerate(remaining_links, start=len(listings_data)+1):
    # Extract the link to the record
    url = link
    driver.get(url)

    data = {}
    try:
        rows = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '//div[@data-sentry-element="ItemGridContainer"]')
            )
        )
        
        for row in rows:
            cells = row.find_elements(By.XPATH, './div')
        
            if len(cells) < 2:
                continue
        
            key = cells[0].text.replace(":", "").strip()
            value = cells[1].text.strip()
        
            data[key] = value
    except:
        print('No element found. Refreshing')
        time.sleep(SLEEP)
        driver.refresh()
        rows = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '//div[@data-sentry-element="ItemGridContainer"]')
            )
        )
        
        for row in rows:
            cells = row.find_elements(By.XPATH, './div')
        
            if len(cells) < 2:
                continue
        
            key = cells[0].text.replace(":", "").strip()
            value = cells[1].text.strip()
        
            data[key] = value
        
            
    
    try:
        price_el = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//strong[@data-cy="adPageHeaderPrice"]')
            )
        )
        data['Cena'] = price_el.text
    except:
        try:
            print('No element found. Refreshing')
            time.sleep(SLEEP)
            driver.refresh()
            # Fallback price (investment listing)
            price_el = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//h3[@data-cy="investment-price"]')
                )
            )
            data['Cena'] = price_el.text
    
        except TimeoutException:
            data['Cena'] = None
        
    
    
    try:
        description_el = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-cy="adPageAdDescription"]')
            )
        )
        data['Opis'] = description_el.text
    except TimeoutException:
        data['Opis'] = None
    
    try:
        location_el = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div.css-pla15i')
            )
        )
        data['lokalizacja'] = location_el.text.strip()
    except TimeoutException:
        data['lokalizacja'] = None
    
    data['url'] = url
    data["Powierzchnia"] = parse_num(data.get("Powierzchnia"))
    data["Czynsz"] = parse_num(data.get("Czynsz"))
    data["Cena"] = parse_num(data.get("Cena"))

    listings_data.append(data)
    
    # Save progress after each listing
    with open(listings_data_file, 'wb') as f:
        pickle.dump(listings_data, f)
    
    if idx % 10 == 0:
        print(f"Progress: {idx}/{len(all_links)} listings scraped. Saved to {listings_data_file}")

# Save listings_data to pickle file
with open(listings_data_file, 'wb') as f:
    pickle.dump(listings_data, f)
print(f"Saved listings_data to {listings_data_file}")

final_df = pd.DataFrame(listings_data)

# Save to CSV with timestamp
csv_filename = f'otodom_listings_{timestamp}.csv'
final_df.to_csv(csv_filename, index=False, encoding='utf-8')
print(f"Saved CSV to {csv_filename}")

ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)