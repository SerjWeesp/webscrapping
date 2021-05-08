# -*- coding: utf-8 -*-
import scrapy

limit100 = True
if limit100 == True:
	limit = 100
else:
	limit = None

class CarsOptionsSpider(scrapy.Spider):
    name = 'cars'
    allowed_domains = ['ebay.com']
    
    try:
        with open("links.csv", "rt") as f:
            start_urls =['https://www.ebay.com/itm/203401079366']*16 + [url.strip() for url in f.readlines()][1:limit]
    except:
        start_urls = []

    def parse(self, response):
        table_raw = response.xpath('//*[@id="viTabs_0_is"]//text()').extract()
        table = [name.strip() for name in table_raw]
        cars = list(filter(None, table))[1:]
        cars = [car.replace(':', '') for car in cars]
        
        if "Seller Notes" in cars:
            del cars[2:6]
        
        if response.xpath('//*[@id="prcIsum"]//text()').extract() == []:
            if response.xpath('//*[@id="prcIsum_bidPrice"]/text()').extract() == []:
                if response.xpath('//*[@class="notranslate vi-VR-cvipPrice"]/text()').extract() == []:
                    prices = ['None']
                else: 
                    prices = response.xpath('//*[@class="notranslate vi-VR-cvipPrice"]/text()').extract()
            else:
                prices = response.xpath('//*[@id="prcIsum_bidPrice"]/text()').extract()
        else: 
            prices = response.xpath('//*[@id="prcIsum"]//text()').extract()
        price = [price.strip() for price in prices]
        
        car_dict = {}
        cars_dict = dict(zip(cars[::2], cars[1::2]))
        cars_dict['Price'] = price

        yield cars_dict

    
