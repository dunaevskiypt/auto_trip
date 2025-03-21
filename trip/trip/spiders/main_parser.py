from .info_car import InfoCarParser
from .location_parser import LocationParser
from .salesman_spider import SalesmanSpiderSpider
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class MainSpider(CrawlSpider):
    name = "main_parser"
    allowed_domains = ["auto.ria.com"]
    start_urls = [
        "https://auto.ria.com/uk/legkovie/?page=1"]

    rules = (
        Rule(LinkExtractor(
            restrict_xpaths="//a[@class='m-link-ticket']"), callback="parse_item", follow=True),
    )

    def __init__(self, *args, **kwargs):
        super(MainSpider, self).__init__(*args, **kwargs)

        # Initialize parsers
        self.location_parser = LocationParser()
        self.info_car_parser = InfoCarParser()
        # Initialize SalesmanSpiderSpider parser
        self.salesman_spider = SalesmanSpiderSpider()

    def parse_item(self, response):
        # Use parsers to process the response
        yield from self.location_parser.parse(response)
        yield from self.info_car_parser.parse(response)
        # Process through salesman_spider
        yield from self.salesman_spider.parse(response)

    def closed(self, reason):
        # Close parsers after finishing work
        self.location_parser.close()
        self.info_car_parser.close()
        self.salesman_spider.close()  # Close salesman_spider
