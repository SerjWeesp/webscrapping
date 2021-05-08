# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 12:25:43 2021

@author: Pavilion
"""

limit100 = True
if limit100 == True:
	limit = 100
else:
	limit = ''

import pandas as pd
import time
from selenium import webdriver
import math
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
caps = DesiredCapabilities.CHROME
caps["pageLoadStrategy"] = "eager"


start_time = time.time()
driver = webdriver.Chrome(desired_capabilities=caps, executable_path=r'D:\\UW\\2nd semester\\Webscrapping\\chromedriver.exe')
driver.get('https://www.ebay.com/b/Auto-Parts-and-Vehicles/6000/')

time.sleep(4)
try:
    driver.find_element_by_xpath('//*[@id="gdpr-banner-accept"]').click() #cookie banner
except:
    pass


try:
    driver.find_element_by_xpath('//*[@id="s0-27_1-9-0-1[1]-0-1-2-14[0[0]]"]').click() #find button
except: 
    driver.find_element_by_xpath('//*[@id="s0-27-9-0-1[1]-0-1-2-14[0[0]]"]').click()

#define brands number                             
brands = []
counter_1 = 2
stop = 0
time.sleep(2)
while stop < 1:
    try:
        brand = driver.find_element_by_xpath('//*[@id="s0-27-9-0-1[0]-0-1-2-CAR_AND_TRUCK_0"]/select/option['+str(counter_1)+']').text
        brands.append(brand)
        counter_1 += 1
    except:
        stop = 1

try:
    brands_num = range(2,len(brands)+2-int(limit*0.89))
except:
    brands_num = range(2,len(brands)+2)

end_time = time.time() - start_time
print(end_time)


#get list of links
start_time0 = time.time()
links = []
for brand in [x for x in brands_num if x !=5 and x != 81]: # except Skoda and Auriel
    time.sleep(3)

    driver.find_element_by_xpath('//*[@id="s0-27-9-0-1[0]-0-1-2-CAR_AND_TRUCK_0"]/select/option['+str(brand)+']').click() #choose manufacturer
    driver.find_element_by_xpath('//*[@id="s0-27-9-0-1[0]-0-1-2-14[0[0]]"]').click() #find button
    #define number of pages
    num_results = driver.find_element_by_xpath('//*[@id="mainContent"]/div[1]/div/div[2]/div[1]/div[1]/h1/span[1]').text
    num_results = int(num_results.replace(',',''))
    last_page = math.ceil(num_results/50)
    
    counter_2 = 1
    while counter_2 <= last_page:
        try:
            for l in range (1, 51):
                try:
                    link = driver.find_element_by_xpath('//*[@id="srp-river-results"]/ul/li['+str(l)+']/div/div[1]/div/a').get_attribute('href')
                    links.append(link)
                except:
                    pass
                       
            if last_page > 2:    
                try:
                    driver.find_element_by_xpath('//*[@id="srp-river-results"]/ul/div[3]/div[2]/span/span/nav/a[2]').click()
                    counter_2 += 1
                except:
                    driver.find_element_by_xpath('//*[@id="srp-river-results"]/ul/div[4]/div[2]/span/span/nav/a[2]').click()
                    counter_2 += 1
            else: 
                 driver.get('https://www.ebay.com/b/Cars-Trucks/6001/bn_1865117?rt=nc&LH_ItemCondition=3000%7C1000%7C2500&_stpos=10025')
                 counter_2 += 1
        except:
            driver.get('https://www.ebay.com/b/Cars-Trucks/6001/bn_1865117?rt=nc&LH_ItemCondition=3000%7C1000%7C2500&_stpos=10025')
            counter_2 += 1
    
    #write the output
    links_df = pd.DataFrame(links)
    links_df.to_csv('D:\\UW\\2nd semester\\Webscrapping\\Project\\links.csv')
    driver.get('https://www.ebay.com/b/Cars-Trucks/6001/bn_1865117?rt=nc&LH_ItemCondition=3000%7C1000%7C2500&_stpos=10025')

end_time0 = time.time() - start_time0
print(end_time0)

#get cars
start_time = time.time()

cars_test = pd.DataFrame()
n = 13
for link in links[:limit]:
    driver.get(link)
    try:
        driver.find_element_by_xpath('//*[@id="gdpr-banner-accept"]').click() #cookie banner
    except:
        pass
  
    col_names = ['Price']
    for i in range(1,n):
        try:
            x = driver.find_element_by_xpath('//*[@id="viTabs_0_is"]/div/table[2]/tbody/tr['+str(i)+']/td[1]').text
            col_names.append(x[:-1])  
            x = driver.find_element_by_xpath('//*[@id="viTabs_0_is"]/div/table[2]/tbody/tr['+str(i)+']/td[3]').text
            col_names.append(x[:-1])
        except:
            try:
                x = driver.find_element_by_xpath('//*[@id="viTabs_0_is"]/div/table/tbody/tr['+str(i)+']/td[1]').text
                col_names.append(x[:-1])
                x = driver.find_element_by_xpath('//*[@id="viTabs_0_is"]/div/table/tbody/tr['+str(i)+']/td[3]').text
                col_names.append(x[:-1])
            except:
                pass
                
    #get price 
    try:    
        try:
            col_values = [driver.find_element_by_xpath('//*[@id="prcIsum"]').text.replace(',','')]
        except:
            try:
                col_values = [driver.find_element_by_xpath('//*[@id="prcIsum_bidPrice"]').text.replace(',','')]
            except:
                col_values = [driver.find_element_by_xpath('//*[@id="mainContent"]/div[1]/table/tbody/tr[6]/td/div/div[2]/div[2]/span').text.replace(',','')]
    except:
        pass
    
    #get values
    for k in range(1,n):
        try:
            x = driver.find_element_by_xpath('//*[@id="viTabs_0_is"]/div/table[2]/tbody/tr['+str(k)+']/td[2]').text
            col_values.append(x)
            x = driver.find_element_by_xpath('//*[@id="viTabs_0_is"]/div/table[2]/tbody/tr['+str(k)+']/td[4]').text
            col_values.append(x)
        except:
            try:
                x = driver.find_element_by_xpath('//*[@id="viTabs_0_is"]/div/table/tbody/tr['+str(k)+']/td[2]').text
                col_values.append(x)
                x = driver.find_element_by_xpath('//*[@id="viTabs_0_is"]/div/table/tbody/tr['+str(k)+']/td[4]').text
                col_values.append(x)
            except:
                pass
        
    #fill data frame
    cars_test = cars_test.append(dict(zip(col_names, col_values)), ignore_index = True)

    #export
    cars_test.to_csv('D:\\UW\\2nd semester\\Webscrapping\\Project\\cars_ford.csv')
    
end_time = time.time() - start_time
print(end_time)

    
    
    