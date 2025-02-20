import scrapy


class InfoCarSpider(scrapy.Spider):
    name = "info_car"
    allowed_domains = ["auto.ria.com"]
    start_urls = ["https://auto.ria.com"]

    def parse(self, response):
        pass
