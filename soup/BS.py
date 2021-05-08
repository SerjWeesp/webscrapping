import requests
from urllib import request
from bs4 import BeautifulSoup as BS
import re
import pandas as pd
import time

limit100 = True
if limit100 == True:
    limit1 = 2
    limit2 = 100
else:
    limit1 = len(brands)
    limit2 = None


start_time = time.time()
url = 'https://www.ebay.com/b/Cars-Trucks/6001/bn_1865117?rt=nc&LH_ItemCondition=3000%7C1000%7C2500&_stpos=10025'
requests.get(url)
page = requests.get(url)
soup = BS(page.text, 'lxml')


tags = soup.find_all('a', class_ = 'b-textlink b-textlink--sibling')
brands = []
for tag in tags:
   brands.append(tag['href'])

end_time = time.time() - start_time
print(end_time)
###############LINKS
start_time0 = time.time()
links = []

for brand in brands[:limit1]:
    url = brand
    requests.get(url)
    page = requests.get(url)
    try:
        while True:
            soup = BS(page.text, 'lxml')
            tags_links = soup.find_all('a', {'href':re.compile('https://www.ebay.com/itm/.*')})
            for i,tag in enumerate(tags_links):
                if i % 2!=0:
                    links.append(tag['href'])
                else:
                    pass 
            next_page = soup.find('a',{'rel':'next'}).get('href')
            page = requests.get(next_page)
    except:
        pass

end_time0 = time.time() - start_time0
print(end_time0)
###############CARS
start_time1 = time.time()
cars_test = pd.DataFrame()
for link in links[:limit2]:
    url = link
    requests.get(url)
    page = requests.get(url)
    soup = BS(page.text, 'lxml')
    
    col_names=['Price']
    tags_cars = soup.find_all('td', class_ = 'attrLabels')
    for car in tags_cars:
        col_names.append(car.get_text(strip=True)[:-1])
    
    
    try:
        col_values = [soup.find('span', {'id':re.compile('prcIsum.*')}).text]
    except:
        col_values = [soup.find('span', {'class':'notranslate vi-VR-cvipPrice'}).text]
    tags_cars = soup.find_all('td', {'width':'50.0%'})
    for car in tags_cars:
        col_values.append(car.get_text(strip=True))    
        
    cars_test = cars_test.append(dict(zip(col_names, col_values)), ignore_index = True)
    cars_test.to_csv('D:\\cars.csv')
end_time1 = time.time() - start_time1
print(end_time1)
    
    

