# -*- coding: utf-8 -*-
"""
Created on Sat Feb 19 23:27:09 2022

@author: Pavilion
"""
import pandas as pd
import numpy as np
import time
from selenium import webdriver
import math
import requests 
from bs4 import BeautifulSoup 
import re
import string
import os

driver = webdriver.Chrome(executable_path=r'D:\\UW\\3rd semester\\Text mining\\chromedriver_win32\\chromedriver.exe')
driver.get('https://www.marketwatch.com/column/coronavirus-update')
time.sleep(3)

try:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    driver.find_element_by_xpath('//*[@id="notice"]/div[4]/div/div/button[2]').click()
except:
    pass

#scrapping list of links
links = []
count = 0



while len(links) < 314:
    try:
        count += 1
        link = driver.find_element_by_xpath('//*[@id="maincontent"]/div[3]/div[1]/div/div/div[1]/div['+str(count)+']/div/h3/a').get_attribute('href')
        links.append(link)

    except:
        SCROLL_PAUSE_TIME = 1

        # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while count < 314:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)
        
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
        driver.find_element_by_xpath('//*[@id="maincontent"]/div[3]/div[1]/div/div/div[2]/button[1]').click()
        
#scrapping every link from the list
data = []

for url in links:
    response=requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    header = soup.find('h1',{'class':"article__headline"}).get_text()
    date = soup.find('time',{'class':"timestamp timestamp--pub"}).get_text()
    body = soup.find('div',{'class':"article__body article-wrap at16-col16 barrons-article-wrap"}).get_text() 
    
    #text formatting
    header = header.replace('\n', '').strip()
    date = date.replace('\n', '').strip().split(': ', 1)[1].split(' at', 1)[0]
    body = body.replace('\n', '').strip().split('See:', 1)[0]
    data.append((date, header, body))

#creating data frame
df = pd.DataFrame(data, columns =['Date', 'Header', 'Body'])
df.to_csv('D:/UW/3rd semester/Text mining/project/news.csv')

