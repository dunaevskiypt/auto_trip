from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from .location_parser import LocationParser  # правильний імпорт LocationParser
from .info_car import InfoCarParser  # додано імпорт InfoCarParser


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

        # Створюємо парсери
        self.location_parser = LocationParser()
        self.info_car_parser = InfoCarParser()  # Створюємо екземпляр InfoCarParser

    def parse_item(self, response):
        # Використовуємо парсери для обробки відповіді
        yield from self.location_parser.parse(response)
        # Додаємо обробку даних для InfoCarParser
        yield from self.info_car_parser.parse(response)

    def closed(self, reason):
        # Закриваємо парсери після завершення роботи
        self.location_parser.close()
        self.info_car_parser.close()  # Закриваємо InfoCarParser
