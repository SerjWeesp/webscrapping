# -*- coding: utf-8 -*-
"""
Created on Fri Apr  1 21:51:30 2022

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
#import yfinance as yf
#from yahoofinancials import YahooFinancials
from selenium import webdriver
import itertools
import time


#getting the list of tickers
url = 'https://www.bankier.pl/inwestowanie/profile/quote.html?symbol=WIG'
response=requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
wig = soup.find('table',{'class':"sortTableMixedData"})
wig_list = pd.read_html(str(wig))[0]
wig_list.loc[wig_list.Ticker == 'OAT', 'Ticker'] = 'MOC' #rename single ticker with its actual name


#########################################################################################################################################
#polish companies financial data scrapping

#for each ticket we get the data from financial statemets
wig_data = pd.DataFrame()
counter = 1

for name in wig_list.Nazwa:
    page = 1
    fin_report = []
    while fin_report is not None:
        url = 'https://www.bankier.pl/gielda/notowania/akcje/'+str(name)+'/wyniki-finansowe/jednostkowy/kwartalny/standardowy/'+str(page)    
        response=requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        try:
            fin_report = soup.find('table')
            df2 = pd.read_html(str(fin_report))[0]
            df2 = df2.transpose().reset_index()
            df2.columns = df2.iloc[0,:]
            df2 = df2.drop(0)
            df2['symbol'] = name
            df2.set_index('symbol', inplace = True)

            wig_data = wig_data.append(df2)
            page += 1
        except:
            pass
    print(counter, name, len(wig_data))
    counter += 1

#data cleaning and formatting
for row in range(len(wig_data)):
    wig_data.iloc[row, 0] = wig_data['Unnamed: 0'][row].replace('IV Q ', '31-12-')
    wig_data.iloc[row, 0] = wig_data['Unnamed: 0'][row].replace('III Q ', '30-09-')
    wig_data.iloc[row, 0] = wig_data['Unnamed: 0'][row].replace('II Q ', '30-06-')
    wig_data.iloc[row, 0] = wig_data['Unnamed: 0'][row].replace('I Q ', '31-03-')
    for col in range(2, len(wig_data.columns)):
        try:
            wig_data.iloc[row,col] = int(re.sub(r'(\d)\s+(\d)', r'\1\2', wig_data.iloc[row,col]))
        except:
            pass

#create the list of clear column names
colnames = ['Date', 'Currency', 'Net sales revenues', 'Profit (loss) on operating activities', 'Gross profit (loss)',
            'Net profit (loss) parent', 'Depreciation', 'EBITDA', 'Assets', 'Equity', 'Number of shares', 'Earnings per share (zl)',
            'Book value per share (zl)']


#banks have different statements, so we can't use it. Banks will be deleted

#list of banks' tickers
banks = ['ALIOR', 'BNPPPL', 'BOS', 'GETIN', 'GETINOBLE', 'HANDLOWY', 'INGBSK', 'MBANK', 'MILLENNIUM',
         'PEKAO', 'PKOBP', 'SANPL', 'SANTANDER', 'UNICREDIT', 'PZU']

wig_data_no_banks = wig_data.loc[[tickname for tickname in np.unique(wig_data.index.values) if tickname not in banks]]
wig_data_no_banks = wig_data_no_banks.iloc[:, 0:13]
wig_data_no_banks.columns = colnames


#delete some inapropriate data with period name Q0000 and Q000.1 
wig_data_no_banks = wig_data_no_banks.reset_index()
wig_data_no_banks.loc[wig_data_no_banks['Date'].str.contains('(?i)0000', na=False) | wig_data_no_banks['Date'].str.contains('\\.', na=False), ].index
wig_data_clean = wig_data_no_banks.drop(wig_data_no_banks.loc[wig_data_no_banks['Date'].str.contains('(?i)Q', na=False) | wig_data_no_banks['Date'].str.contains('\\.', na=False), ].index)
wig_data_clean.reset_index(drop = True, inplace = True)

#save to csv
wig_data_clean.to_csv('D:/UW/4 semester/Empirics/project/wig_data.csv')
#wig_data_clean = pd.read_csv('D:/UW/4 semester/Empirics/project/wig_data.csv')


#########################################################################################################################################
#polish companies market data scrapping

#setting up Selenium driver
driver = webdriver.Chrome(executable_path=r'D:\\UW\\2nd semester\\Webscrapping\\chromedriver.exe')
url = 'https://stooq.com/q/d/?s=BMC&i=q&l=1'

###YOU HAVE 20 SEC ENTER CAPTCHA AND CHOOSE QUARTERLY DATA BULLET AND PRESS SHOW BUTTON###
driver.get(url)
driver.find_element_by_xpath('/html/body/div/div[2]/div[1]/div[2]/div[2]/button[1]').click()  #cookies
time.sleep(20)

#for each company from wig_list we scrap stock market data and append to final data frame
wig_stocks = pd.DataFrame()
for ticker in wig_list.Ticker:
    list_to_df = []
    try:
        for page_num in range(1,5):
            url = 'https://stooq.com/q/d/?s='+str(ticker)+'&i=q&l='+str(page_num)
            driver.get(url)
            text = driver.find_element_by_xpath('//*[@id="fth1"]').text
            text_df = text.split()[8:]   
            #the next chunk excludes from scrapping dividends, splitting and etc.
            for item in text_df:
                if item in ['Split','Dividend', 'Other'] and text_df[text_df.index(item)+2] in ['Preemptive', 'Prepurchase', 'Preaccession']:
                    del text_df[text_df.index(item)-3:text_df.index(item)+6]
                else:
                    if item in ['Preemptive','Prepurchase','Preaccession'] and text_df[text_df.index(item)+3] in ['Preemptive','Prepurchase','Preaccession']:
                        del text_df[text_df.index(item)-3:text_df.index(item)+7]
                    else:
                        if item in ['Preemptive','Prepurchase','Preaccession'] and text_df[text_df.index(item)+3] in ['Split','Dividend', 'Other']:
                            del text_df[text_df.index(item)-3:text_df.index(item)+6]
                        else:
                            if item in ['Split','Dividend', 'Other'] and text_df[text_df.index(item)+2] in ['Split','Dividend', 'Other']:
                                del text_df[text_df.index(item)-3:text_df.index(item)+5]
                            else:
                                if item in ['Split','Dividend', 'Other']:
                                    del text_df[text_df.index(item)-3:text_df.index(item)+3]
                                else:
                                    if item in ['Preemptive', 'Prepurchase', 'Preaccession']:
                                        del text_df[text_df.index(item)-3:text_df.index(item)+4]
                                        
            n = 11 
            list_to_add = [text_df[i:i + n] for i in range(0, len(text_df), n)]
            list_to_df.append(list_to_add)
            
    except:
        try:
            if driver.find_element_by_xpath('//*[@id="l"]/a').text == 'Change code':
                time.sleep(30)
                text = driver.find_element_by_xpath('//*[@id="fth1"]').text
                text_df = text.split()[8:]   
                for item in text_df:
                    if item in ['Split','Dividend', 'Other'] and text_df[text_df.index(item)+2] in ['Preemptive', 'Prepurchase', 'Preaccession']:
                        del text_df[text_df.index(item)-3:text_df.index(item)+6]
                    else:
                        if item in ['Preemptive','Prepurchase','Preaccession'] and text_df[text_df.index(item)+3] in ['Preemptive','Prepurchase','Preaccession']:
                            del text_df[text_df.index(item)-3:text_df.index(item)+7]
                        else:
                            if item in ['Preemptive','Prepurchase','Preaccession'] and text_df[text_df.index(item)+3] in ['Split','Dividend', 'Other']:
                                del text_df[text_df.index(item)-3:text_df.index(item)+6]
                            else:
                                if item in ['Split','Dividend', 'Other'] and text_df[text_df.index(item)+2] in ['Split','Dividend', 'Other']:
                                    del text_df[text_df.index(item)-3:text_df.index(item)+5]
                                else:
                                    if item in ['Split','Dividend', 'Other']:
                                        del text_df[text_df.index(item)-3:text_df.index(item)+3]
                                    else:
                                        if item in ['Preemptive', 'Prepurchase', 'Preaccession']:
                                            del text_df[text_df.index(item)-3:text_df.index(item)+4]
                n = 11 #number of variables
                list_to_add = [text_df[i:i + n] for i in range(0, len(text_df), n)]
                list_to_df.append(list_to_add)
            
            else:
                pass
        
        except:
            pass
    
    #data pre-formatting
    flat_list = itertools.chain(*list_to_df)
    flat_list = list(flat_list)
    
    stock_df = pd.DataFrame(flat_list, columns = ['No', 'day','mon', 'year', 'open', 'high', 'low', 'close', 'perc_change',
                                                   'abs_change', 'vol'])
    stock_df['Ticker'] = ticker
    stock_df.loc[stock_df.No == '1', 'vol'] = stock_df.loc[stock_df.No == '1', 'perc_change']
    stock_df.loc[stock_df.No == '1', 'perc_change'] = None
    
    wig_stocks = wig_stocks.append(stock_df)

#dates reformatting
def dates_format(df):
    df.loc[df.mon == 'Dec', 'mon'] = '12'
    df.loc[df.mon == 'Mar', 'mon'] = '03'
    df.loc[df.mon == 'Jun', 'mon'] = '06'
    df.loc[df.mon == 'Sep', 'mon'] = '09'
    df["period"] = df["day"] +'-'+ df["mon"] +'-'+ df["year"]
    df.drop(['day','mon','year'], axis = 1, inplace = True)
    return df

wig_stocks = dates_format(wig_stocks)

#save to csv
wig_stocks.to_csv('D:/UW/4 semester/Empirics/project/wig_stocks.csv') 

#load
#wig_stocks = pd.read_csv('D:/UW/4 semester/Empirics/project/wig_stocks.csv')

#########################################################################################################################################
#wig market data scrapping

#setting up selenium driver
driver = webdriver.Chrome(executable_path=r'D:\\UW\\2nd semester\\Webscrapping\\chromedriver.exe')
url = 'https://stooq.com/q/d/?s=wig&c=0&i=q'
driver.get(url)
driver.find_element_by_xpath('/html/body/div/div[2]/div[1]/div[2]/div[2]/button[1]').click()  #cookies
text = driver.find_element_by_xpath('//*[@id="fth1"]').text
text_df = text.split()[8:]   
list_to_df = []
for page_num in range(1,5):
    url = 'https://stooq.com/q/d/?s=wig&i=q&l='+str(page_num)
    driver.get(url)
    text = driver.find_element_by_xpath('//*[@id="fth1"]').text
    text_df = text.split()[8:]   
    n = 11 
    list_to_add = [text_df[i:i + n] for i in range(0, len(text_df), n)]
    list_to_df.append(list_to_add)
    flat_list = itertools.chain(*list_to_df)
    flat_list = list(flat_list)

wig_df = pd.DataFrame(flat_list, columns = ['No', 'day','mon', 'year', 'open', 'high', 'low', 'close', 'perc_change',
                                               'abs_change', 'vol'])
#dates formatting
wig_df = dates_format(wig_df)

#########################################################################################################################################
#merge all datasets into final data frame

final_df = wig_stocks.merge(wig_df,  how='inner', on='period', suffixes=('','_wig'))
final_df = pd.merge(final_df, wig_list,  how='inner', left_on=['Ticker'], right_on = ['Ticker'])
final_df = pd.merge(final_df, wig_data_clean,  how='inner', left_on=['Nazwa', 'period'], right_on = ['symbol','Date'])
final_df.to_csv('D:/UW/4 semester/Empirics/project/final_df_long.csv') 

#sorting and cleaning: we took only data in PLN and excluded the first historical records, because they are not suitable for our research 
final_df_sorted = final_df.loc[final_df['Currency']=='PLN',]
final_df_sorted.loc[final_df_sorted['Assets']==0, 'Assets'] = None
final_df_sorted.dropna(inplace = True)

#selecting from final dataset only target variables
final_df_short = final_df_sorted.loc[:, ['Ticker','period', 'close', 'perc_change', 'close_wig', 
                                         'perc_change_wig', 'Assets', 'Number of shares']]
#final_df_short.to_csv('D:/UW/4 semester/Empirics/project/final_df_short_ret.csv') 


miss_data = ['BNP'] #list of tickers to be excluded from final df due to some data errors
final_df_short = final_df_short.loc[-final_df_short['Ticker'].isin(miss_data),]
final_df_short.to_csv('D:/UW/4 semester/Empirics/project/final_df_short_ret_clean.csv') 




