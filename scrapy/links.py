# -*- coding: utf-8 -*-
import scrapy


class Link(scrapy.Item):
    link = scrapy.Field()
   
class LinksSpider(scrapy.Spider):
    name = 'links'
    allowed_domains = ['ebay.com']
    try:
        with open("brands.csv", "rt") as f:
            start_urls = [url.strip() for url in f.readlines()][2:]
    except:
        start_urls = [] 

    def parse(self, response):
        for cell in range(1, 49):
            l = Link()
            try:
                if response.xpath('//*[@id="s0-27-9-0-1[0]-0-1"]/ul/li['+str(cell)+']/div/div[1]/div/a//@href').extract_first() is None:
                    l['link'] = response.xpath('//*[@id="s0-27_1-9-0-1[0]-0-1"]/ul/li['+str(cell)+']/div/div[1]/div/a//@href').extract_first()
                else:
                    l['link'] = response.xpath('//*[@id="s0-27-9-0-1[0]-0-1"]/ul/li['+str(cell)+']/div/div[1]/div/a//@href').extract_first()
                if l['link'] is not None:
                    yield l
            except:
                pass
        next_page_url = response.xpath('//*[@id="s0-27-9-0-1[0]-0-1-37-11-1"]/a[2]//@href').extract_first()
        absolute_next_page_url = response.urljoin(next_page_url)
        yield scrapy.Request(absolute_next_page_url)



