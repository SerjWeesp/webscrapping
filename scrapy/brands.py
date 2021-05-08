# -*- coding: utf-8 -*-
import scrapy

class Link(scrapy.Item):
    link = scrapy.Field()

class BrandsSpider(scrapy.Spider):
    name = 'brands'
    allowed_domains = ['ebay.com']
    start_urls = ['https://www.ebay.com/b/Cars-Trucks/6001/bn_1865117?rt=nc&LH_ItemCondition=3000%7C1000%7C2500&_stpos=10025']
    

    def parse(self, response):
        for brand in range(2, 23):
            l = Link()
            l['link'] = response.xpath('//*[@id="s0-16-13-0-1[0]-0-0"]/ul/li['+str(brand)+']/a//@href').extract()
            yield l

        for brand in range(1, 72):
            l = Link()
            l['link'] = response.xpath('//*[@id="s0-16-13-0-1[0]-0-0"]/ul/li[23]/ul/li['+str(brand)+']//@href').extract()
            yield l









    


    