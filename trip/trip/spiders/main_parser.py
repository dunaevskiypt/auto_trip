from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from .location_parser import LocationParser  # правильний імпорт LocationParser


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

        # Створюємо парсер Location
        self.location_parser = LocationParser()

    def parse_item(self, response):
        # Використовуємо парсер Location для обробки відповіді
        yield from self.location_parser.parse(response)

    def closed(self, reason):
        # Закриваємо парсер після завершення роботи
        self.location_parser.close()
