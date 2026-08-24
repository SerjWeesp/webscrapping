# -*- coding: utf-8 -*-
"""
Created on Sun Jan 11 18:24:44 2026

@author: Dell
"""

# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""


import time
import os
import re
import math
import pickle
import pandas as pd
import googlemaps
import datetime
today = str(datetime.date.today()) 
from datetime import datetime
import ctypes
from dotenv import load_dotenv



# Load environment variables from the .env file in the same directory as this script
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.edge.service import Service as EdgeService

ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)

SLEEP = 10
# Read the key from an environment variable instead of storing it in source control.
api_key = os.getenv("GOOGLE_MAPS_API_KEY")
if not api_key:
    raise RuntimeError("Set the GOOGLE_MAPS_API_KEY environment variable before running.")
edge_driver_path = r'C:\Users\Dell\Downloads\msedgedriver.exe'

# Generate timestamp in ddmmyyyy format (e.g., "22082026"). Used to unique-name today's scrape files.
timestamp = datetime.now().strftime('%d%m%Y') 

# Stores the complete list of collected listing URLs to allow resuming the link gathering phase.
all_links_file = f'output_otodom/all_links_{timestamp}.pkl'

# Tracks page numbers (1, 2, 3...) that have been fully scraped to resume pagination progress if stopped.
processed_pages_file = f'output_otodom/processed_pages_{timestamp}.pkl'

# Periodically saves the actual detailed listing data (price, size, travel times, etc.) to prevent data loss.
listings_data_file = f'output_otodom/listings_data_{timestamp}.pkl'

def calculate_travel_time(address, destination_address, key, mode="transit", departure_time=None):
    """
    Calculates the travel time between two addresses using the Google Maps Directions API.

    Parameters:
    -----------
    address : str
        The starting address (origin) for the route calculation.
    destination_address : str
        The destination address (target) for the route calculation.
    key : str
        The Google Maps API key used to authenticate with the service.
    mode : str, optional
        The transport mode to use. Supported options are "driving", "walking", 
        "bicycling", or "transit" (default).
    departure_time : datetime, optional
        The time of departure to get transit schedules or traffic estimates. 
        Defaults to the current system time if None.

    Returns:
    --------
    str
        A human-readable string indicating the travel duration (e.g., "25 mins") if a route is found,
        'No route found' if a route is unavailable, or an error message if the API request fails.
    """
    if not address or not destination_address:
        return 'Invalid address'

    if departure_time is None:
        departure_time = datetime.now()

    gmaps = googlemaps.Client(key=key)
    try:
        # Calculate travel time between two destinations using specified mode
        directions_result = gmaps.directions(address,
                                              destination_address,
                                              mode=mode,
                                              departure_time=departure_time)
        
        # Extract travel time
        if directions_result:
            return directions_result[0]['legs'][0]['duration']['text']
        else:
            return 'No route found'
    except googlemaps.exceptions.ApiError as e:
        # Handle API errors gracefully
        print(f"API Error: {e.status}")
        return f'API Error: {e.status}'
    except Exception as e:
        print(f"Error calculating travel time: {e}")
        return 'Error'
    
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

def close_cookie_banner(driver):
    """
    Attempts to close the cookie banner by rejecting all cookies via JavaScript.
    Can be called repeatedly as banners may reappear on different pages.
    """
    try:
        # Try to reject cookies using the reject all handler if available via JS
        driver.execute_script('const el = document.querySelector("#onetrust-reject-all-handler"); if(el) { el.click(); }')
    except Exception:
        pass

    # Fallback to accepting if rejection handler was not found or failed
    try:
        accept_btn = driver.find_elements(By.ID, 'onetrust-accept-btn-handler')
        if accept_btn:
            accept_btn[0].click()
    except Exception:
        pass


# Set up Edge WebDriver with optimal options for safe and efficient scraping
options = webdriver.EdgeOptions()

# --- EFFICIENCY CONFIGURATION ---
# Disable image loading to save massive bandwidth and speed up page load times
options.add_argument("--blink-settings=imagesEnabled=false")
# Disable background network activity not related to loading the page
options.add_argument("--disable-background-networking")
# Disable component updates to prevent automatic downloads during scraping
options.add_argument("--disable-component-update")
# Disable cloud sync to free up CPU and network overhead
options.add_argument("--disable-sync")
# Disable GPU hardware acceleration (saves RAM and CPU, highly recommended for servers/headless)
options.add_argument("--disable-gpu")
# Mute all audio to prevent background noise and save processing resources
options.add_argument("--mute-audio")
# Avoid potential Linux/Docker shared memory crashes (good practice for cross-platform)
options.add_argument("--disable-dev-shm-usage")
# Page load strategy: 'eager' tells the driver to proceed once DOM is ready (HTML loaded), 
# without waiting for heavy external assets like ads, tracking scripts, and images.
options.page_load_strategy = 'eager'

# --- SAFETY & ANTI-DETECTION CONFIGURATION ---
# Run in modern headless mode (runs in the background without opening a physical window)
# options.add_argument("--headless=new")

# Set a realistic user-agent string so the browser doesn't identify as a default Selenium bot
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edge/120.0.0.0")

# Hide the automated test software banner ("Edge is being controlled by...")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

# Disable automation detection flags like navigator.webdriver
options.add_argument("--disable-blink-features=AutomationControlled")

# Specify the Edge WebDriver executable path
driver = webdriver.Edge(service=EdgeService(edge_driver_path), options=options)

# URL of the website you want to scrape
url = 'https://www.otodom.pl'
# Open the website
driver.get(url)
close_cookie_banner(driver)


distanceRadius = 0
priceMax=1200000
priceMin=0
areaMin=65
areaMax=200
buildYearMin = 2014
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
time.sleep(1)  # Allow time for the page to load before attempting to close the cookie banner 
close_cookie_banner(driver)

try:
    element = driver.find_element(By.CSS_SELECTOR, '[data-sentry-component="ItemsCounter"]')
    text = element.text.strip()
    match = re.search(r'z\s+(\d+)', text)  # Looks for 'z ' followed by digits
    if match:
        max_pages = math.ceil(int(match.group(1)) / 72)
except:
    pass

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
    close_cookie_banner(driver)

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
    close_cookie_banner(driver)

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
    except TimeoutException:
        print('No element found. Refreshing')
        time.sleep(SLEEP)
        try:
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
        except TimeoutException:
            print("Still no elements after refresh. Skipping.")
            pass

    try:
        price_el = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//strong[@data-cy="adPageHeaderPrice"]')
            )
        )
        data['Cena'] = price_el.text
    except:
        try:
            # Fallback price (investment listing)
            price_el = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//h3[@data-cy="investment-price"]')
                )
            )
            data['Cena'] = price_el.text
    
        except TimeoutException:
            pass

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
        try:
            # Fallback location selector as requested
            location_el = driver.find_element(By.CSS_SELECTOR, '#__next > div.css-2wgx6l.efze3g60 > main > div.css-tn073k.enod22p0 > div.css-1w41ge1.enod22p1 > div.css-144mnth.e1k564jc0 > div.css-70qvj9.e1aypsbg0 > a')
            data['lokalizacja'] = location_el.text.strip()
        except:
            data['lokalizacja'] = None
    
    data['url'] = url
    data["Powierzchnia"] = parse_num(data.get("Powierzchnia"))
    data["Czynsz"] = parse_num(data.get("Czynsz"))
    data["Cena"] = parse_num(data.get("Cena"))
    data['Dojazd do centrum'] = calculate_travel_time(data.get('lokalizacja'), 'Warszawa, Rondo Daszyńskiego', key=api_key, departure_time=datetime(2026, 8, 24, 7, 00, 49, 328478))

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
csv_filename = f'/output_otodom/otodom_listings_{timestamp}.csv'
final_df.to_csv(csv_filename, index=False, encoding='utf-8')
print(f"Saved CSV to {csv_filename}")

ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)