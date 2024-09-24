import pandas as pd 
import requests 
from bs4 import BeautifulSoup 
from selenium import webdriver
import time
import yfinance as yf
from yahoofinancials import YahooFinancials
import missingno as mno
from datetime import datetime, timedelta


#List of SP500 companies
wikiurl="https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
response=requests.get(wikiurl)

soup = BeautifulSoup(response.text, 'html.parser')
sp500=soup.find('table',{'class':"wikitable"})
sp500=pd.read_html(str(sp500))
sp500=pd.DataFrame(sp500[0])
names = sp500['Symbol']
sp500.to_csv('D:/UW/Master/data/sp500.csv')

#Stock data
price = pd.DataFrame()
count = 0

for name in names.str.replace('.','-'):
    tickerData = yf.Ticker(name)
    tickerDf = tickerData.history(period='max', interval='1mo')
    tickerDf = tickerDf.reset_index()
    tickerDf['QUARTER'] = pd.PeriodIndex(tickerDf['Date'], freq='Q')
    tickerDf['MONTH'] = pd.DatetimeIndex(tickerDf['Date']).month
    tiker_mon = tickerDf.loc[tickerDf['MONTH'].isin([1,4,7,10]),].dropna()
    ticker_div = tickerDf.groupby('QUARTER')['Dividends', 'Volume'].sum()
    ticker_range = tickerDf.groupby('QUARTER')['High'].max() - tickerDf.groupby('QUARTER')['Low'].min()
    ticker_range.rename('Range', inplace = True)
    ticker_merge = tiker_mon.merge(ticker_range.reset_index(), how = 'left', on=['QUARTER'])
    ticker_merge =  ticker_merge.merge(ticker_div.reset_index(), how = 'left', on=['QUARTER'])
    ticker_merge['COMPANY'] = name
    ticker_final = ticker_merge[['QUARTER', 'COMPANY', 'Open', 'Range', 'Dividends_y', 'Volume_y']]
    ticker_final.columns = ['QUARTER', 'COMPANY', 'Open', 'Range', 'Dividends', 'Volume']
    price = price.append(ticker_final)
    count += 1
    print(count, str(name)+' is done. Total number: ', len(price))

price = price.reset_index()
price['Date'] = pd.to_datetime(price['Date']).dt.date

'''    
price_sum = price[['COMPANY', 'SECTOR', 'Close']]
price_sum = price_sum.dropna()
price_sum['QUARTER'] = pd.PeriodIndex(price_sum.index, freq='Q')
price_sum = price_sum.groupby(['COMPANY','SECTOR','QUARTER'])['Close'].median()
price_sum = price_sum.reset_index()


#dividends
divd = price[['COMPANY', 'SECTOR', 'Dividends', 'Volume']]
divd = divd.dropna()
divd['QUARTER'] = pd.PeriodIndex(divd.index, freq='Q')
divd = divd.groupby(['COMPANY','SECTOR','QUARTER'])['Dividends', 'Volume'].sum()
divd = divd.reset_index()

result0 = pd.merge(divd, price_sum, on=["COMPANY", "QUARTER", 'SECTOR'])
result0 = result0.reset_index()
result0.drop('index', axis = 1, inplace = True)
'''

#financial data
df = pd.DataFrame()
variables = ['revenue','shares-outstanding', 'net-income', 'total-assets', 'total-liabilities', 'cash-on-hand', 'total-share-holder-equity', 'number-of-employees']
headers = {
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
}
for var in variables:
    count = 0
    print(var)
    for name in names.str.replace('-','.'):
        url = "https://www.macrotrends.net/stocks/charts/"+str(name)+"/apple/"+str(var)
        try:
            response=requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            value = soup.find_all('table',{'class':"table"})
            value = pd.read_html(str(value))
            value = pd.DataFrame(value[0])
            value.columns = ['Date', 'Amount']
            value['Variable'] = var
            value['COMPANY'] = name
            value['SECTOR'] = sp500.loc[count, 'GICS Sector']
            df = df.append(value)
            value = None
        except:
            pass
        print(count, str(name)+' is done. Total number of records: ', len(df))
        count += 1

df = pd.read_csv('D:/UW/Master/data/df.csv')
df['Date'] = pd.to_datetime(df['Date']).dt.date
df['QUARTER'] = pd.PeriodIndex(df['Date'], freq='Q')
merged_df = df.merge(price,how = 'left', on=['QUARTER','COMPANY'])
#df.to_csv('D:/UW/Master/data/df.csv') 



df_wide = df.copy()
df_wide['Amount'] = df_wide['Amount'].str.strip('$').str.replace(',', '')
df_wide['Amount'] = df_wide['Amount'].astype('float')
df_wide['Date'] = pd.to_datetime(df_wide['Date'], format = '%Y/%m/%d')
df_wide['QUARTER'] = pd.PeriodIndex(df_wide['Date'], freq='Q')
df_wide = df_wide.pivot_table(index=['QUARTER', 'COMPANY'], columns='Variable', values=['Amount'], aggfunc='first')
df_wide = df_wide.droplevel(0, axis = 1)
df_wide.reset_index(inplace = True)

result = pd.merge(df_wide, price, on=["COMPANY", "QUARTER"])
result = result.merge(sp500, left_on = 'COMPANY', right_on = 'Symbol')
mno.matrix(result, figsize = (20, 6))
result.isna().sum()

result.to_csv('D:/UW/Master/data/result.csv') 


#############################################################################


'''
#Net income
inc = pd.DataFrame()
count = 0
for name in names.str.replace('-','.'):
    incurl="https://www.macrotrends.net/stocks/charts/"+str(name)+"/mcdonalds/net-income"
    response=requests.get(incurl)
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        income = soup.find_all('table',{'class':"table"})
        income = pd.read_html(str(income))
        income = pd.DataFrame(income[1])
        income.columns = ['Date', 'Amount']
        income['COMPANY'] = name
        income['SECTOR'] = sp500.loc[count, 'GICS Sector']
        inc = inc.append(income)
    except:
        pass
    print(count, str(name)+' is done. Total number: ', len(inc))
    count += 1
inc.to_csv('D:/UW/Master/data/income.csv') 

#revenue
rev = pd.DataFrame()
count = 0
for name in names.str.replace('-','.'):
    revurl="https://www.macrotrends.net/stocks/charts/"+str(name)+"/mcdonalds/revenue"
    response=requests.get(revurl)
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        revenue = soup.find_all('table',{'class':"table"})
        revenue = pd.read_html(str(revenue))
        revenue = pd.DataFrame(revenue[1])
        revenue.columns = ['Date', 'Amount']
        revenue['COMPANY'] = name
        revenue['SECTOR'] = sp500.loc[count, 'GICS Sector']
        rev = rev.append(revenue)
    except:
        pass
    print(count, str(name)+' is done. Total number: ', len(rev))
    count += 1
rev.to_csv('D:/UW/Master/data/revenue.csv') 
'''
#Dividends data
dividends = pd.DataFrame()
count = 0
driver = webdriver.Chrome(executable_path=r'D:\\UW\\2nd semester\\Webscrapping\\chromedriver.exe')

for name in names:

    url = 'https://www.nasdaq.com/market-activity/stocks/'+str(name)+'/dividend-history'
    driver.get(url)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    #time.sleep(3)
    try:
        driver.find_element_by_xpath('//*[@id="onetrust-accept-btn-handler"]').click() #cookie banner
    except:
        pass
    soup = BeautifulSoup(driver.page_source, 'lxml')
    try:
        tables = soup.find_all('table')
        df = pd.read_html(str(tables))    
        df = pd.DataFrame(df[0])
        df['COMPANY'] = name
        df['SECTOR'] = sp500.loc[count, 'GICS Sector']
    except:
        pass
    dividends = dividends.append(df)
    print(count, str(name)+' is done. Total number: ', len(dividends))
    count += 1

#dividends.to_csv('D:/UW/Master/data/dividends.csv')
