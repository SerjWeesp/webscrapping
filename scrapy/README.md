To run spider open terminal, change directopy to your scrapy project and run spiders with command 'scrapy crawl <name>'
If you want to save output in csv file then run spiders with command 'scrapy crawl <name> -o <name>.csv'

Firstly run brands.py spider
Then run links.py spider

In cars.py select limit option:
Select limit100 = True if you want to limit scrapped data to 100 units

Select limit100 = False if you want scrapper to get all data

Finally run cars.py spider
