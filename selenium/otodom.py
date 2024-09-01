# -*- coding: utf-8 -*-
"""
Created on Sat Mar  9 16:23:57 2024

@author: Pavilion
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import pandas as pd
import numpy as np
from unidecode import unidecode
import googlemaps
import datetime
today = str(datetime.date.today())
from datetime import datetime


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
    
api_key = ''  
edge_driver_path = 'D:\Extra study\edgedriver_win64\msedgedriver.exe'

# Set up Edge WebDriver
options = webdriver.EdgeOptions()
options.use_chromium = True

# Specify the Edge WebDriver executable path
driver = webdriver.Edge()

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
priceMax=950000
priceMin=600000
areaMin=45
areaMax=80
buildYearMin = 1950
roomsNumber = '%5BTHREE%2CFOUR%5D'
buildYearMax = 2023

listings_combined =[]

# Iterate through the pages and open each page in a new window
for page in range(1, 18): #page number
    # Construct the URL
    url =f'https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?distanceRadius={distanceRadius}&limit=72&ownerTypeSingleSelect=ALL&priceMax={priceMax}&buildYearMin={buildYearMin}&priceMin={priceMin}&areaMin={areaMin}&areaMax={areaMax}&roomsNumber={roomsNumber}&buildYearMax={buildYearMax}&by=DEFAULT&direction=DESC&viewType=listing&page={page}'
    # Open the URL in a new window
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)

    time.sleep(3)

    # Close Cookies banner
    if not is_banner_closed:
        try:
            cookie_banner = driver.find_element(By.ID,'onetrust-accept-btn-handler')
            cookie_banner.click()
            is_banner_closed = True
        except:
            pass

    # Scroll page down till the end
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Wait for the results to load
    #WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@role='navigation']")))


    # Scroll down to the end of the page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(driver.page_source, features="html.parser")

    # Find all the relevant information
    listings = soup.find_all('article', {'data-cy': 'listing-item'})
    listings_combined.append({'page': page, 'listings': listings})


data = []
rooms = area = floor = None

for item in listings_combined:
    listings = item['listings']
    for record in listings:

    # Extract the link to the record
        link = record.find("a", {'data-testid':'listing-item-link'}).get("href")
        link = "https://www.otodom.pl"+link
        
    # Extract the title
        property_title = record.find('p', {'data-cy': 'listing-item-title'}).get_text()

    # Extract the Offerer
        offerer = record.find_all('div')[-2].get_text()

    # Extract the Address
        address = record.find('p', {'data-testid': 'advert-card-address'}).get_text()
        
    # Extract the other details
        price_element = record.find('div', {'data-testid': 'listing-item-header'})
        price = price_element.get_text().replace('\xa0', '').split('zł')[0].strip() if price_element else None


    # Extract the number of rooms, area, and price
        # Initialize default values for rooms, area, and floor
        rooms = area = floor = 'N/A'  # 'N/A' can be replaced with any suitable default value
        
        # Find the 'div' that contains the details
        specs_list = record.find('div', {'data-testid': 'advert-card-specs-list'})
        
        if specs_list:
            # Extract all 'dd' elements within the specs_list
            details = specs_list.find_all("dd")
        
            # Loop through the details and assign values based on the index
            for idx, detail in enumerate(details[:3]):
                detail_text = detail.get_text().strip()  # Get the text content and strip any leading/trailing whitespace
                
                if idx == 0:  # Assuming the first 'dd' always contains room information
                    rooms = detail_text.replace(" pokoje", "")
                elif idx == 1:  # Assuming the second 'dd' always contains area information
                    area = detail_text.replace(" m²", "")
                elif idx == 2:  # Assuming the third 'dd' always contains floor information
                    floor = detail_text.replace(" piętro", "")
        
        try:
            price_m2 = int(price)/float(area)    
        except:
            price_m2 = 'NA'

        # Append the attributes to the data list
        data.append({
            "Link": link,
            "Property": property_title,
            "Address": address,
            "Rooms": rooms,
            "Area (m²)": area,
            "Price (zł)": price,
            "Price (zł/m2)": price_m2,
            "Offerer": offerer,
            "Piętro": floor
        })



# Create a dataframe from the data list
df = pd.DataFrame(data)

keys = [
    "Czynsz", "Forma własności", "Stan wykończenia", "Balkon / ogród / taras", "Miejsce parkingowe", "Ogrzewanie", 
    "Dostępne od", "Rok budowy", "Rodzaj zabudowy", "Okna", "Winda", 
    "Media", "Zabezpieczenia", "Wyposażenie", "Typ ogłoszeniodawcy",
    "Materiał budynku", "Opis"
]

keys_no_sib = ["Data dodania", "Data aktualizacji"]
    
for index, row in df.iterrows():
    # Extract link from the row
    link = row['Link']

    # Use Selenium to open the page
    driver.get(link)

    # Get the page source after JavaScript has been executed
    page_source = driver.page_source

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Initialize an empty dictionary to hold the extracted values
    extracted_values = {}
    
    # Iterate through the keys and extract their corresponding values from the HTML content
    for key in keys:
        # Search for elements that might contain the key. We'll look for divs and spans that contain the key text.
        elements = soup.find_all(['div', 'span', 'h2'], string=lambda text: text and key in text)
        
        value = "Not Found"
        for element in elements:
            # Attempt to find the next sibling or parent's next sibling that could contain the value
            next_sibling = element.find_next_sibling()
            if not next_sibling:
                next_sibling = element.parent.find_next_sibling()
            if next_sibling:
                value = next_sibling.get_text().strip()
                break  # Break the loop if a value is found
        
        extracted_values[key] = value

    for key in keys_no_sib:
        try:
            value = soup.find_all(['div', 'span', 'h2'], string=lambda text: text and key in text)
            extracted_values[key] = value
        except:
            extracted_values[key] = "Not Found"
    
    try:
        extracted_values['Rynek'] = soup.find('div', {'data-testid':'table-value-market'}).get_text()
    except:
        extracted_values['Rynek'] = 'pierwotny?'
    
    for key, value in extracted_values.items():
        df.at[index, key] = value
        extracted_values[key] = value

features_list = ['Wanna', 'Ogródek', 'Taras', 'Balkon', 'Garderoba', 'Nowe', 'Rezerwacja', 'Prysznic', 'Pompa', 'Fotowoltaika', "Metro", "Tramwaj", "SKM", "PKP"]

# Initialize feature columns to 0
for feature in features_list:
    df[feature] = 0

# Update the DataFrame based on the 'Opis' column
for feature in features_list:
    # The case=False parameter makes the search case-insensitive
    df.loc[df['Opis'].str.contains(feature, case=False, na=False), feature] = 1

remont_phrases = 'po remoncie|wyremontowane|wykończone|świeże|odświeżone|remontowane|odnowione|wymienione|wymieniony'
df['Remont'] = df['Opis'].str.contains(remont_phrases, case=False, na=False, regex=True).astype(int)

agd_phrases = 'agd|wyposarzone'
df['AGD'] = df['Opis'].str.contains(remont_phrases, case=False, na=False, regex=True).astype(int)

dev_phrases = 'deweloperski|developerski|stan deweloperski|do wykończenia|do wykonczenia|w stanie developerskim|w stanie deweloperskim'
df['Stan developerski'] = df['Opis'].str.contains(dev_phrases, case=False, na=False, regex=True).astype(int)

#df.drop_duplicates(inplace = True)
#df.columns = df.columns.str.replace(' ', '')
for column in df.select_dtypes(include=[object]).columns:
    df[column] = df[column].apply(lambda x: unidecode(x) if isinstance(x, str) else x)
df.columns = [unidecode(col) if isinstance(col, str) else col for col in df.columns]

df.dropna(subset = ['Address'], inplace = True)
work = 'Rondo Daszynskiego, Warszawa'
df['Travel Time to Destination'] = df['Address'].apply(lambda x: calculate_travel_time(address=x, destination_address=work, 
                                                                                       departure_time=datetime(2024, 3, 27, 7, 30, 31, 342701), key = api_key))
df['Status'] = 'New'
df['Dzielnica'] = df['Address'].str.split(',').str[-3]
df['Date scrapped'] = today

try:
    df_exist = pd.read_csv('flats_time.csv')
    df_exist['Status'] = 'Present'
    df['Status'] = np.where(df['Link'].isin(df_exist['Link']), 'Present', 'New')
    df_all = pd.concat([df ,df_exist], ignore_index = True)
except:
    df_all = df.copy()

df_all.drop_duplicates(subset='Link', keep='first', inplace = True)
df.to_csv('flats_time_'+today+'.csv', encoding='utf-8')
df_all.to_csv('flats_time.csv')
driver.close()
#os.system("taskkill /f /im pythonw.exe")


