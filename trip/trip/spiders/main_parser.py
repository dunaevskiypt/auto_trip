from .info_car import InfoCarParser
from .location_parser import LocationParser
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

        # Создаем парсеры
        self.location_parser = LocationParser()
        self.info_car_parser = InfoCarParser()

    def parse_item(self, response):
        # Используем парсеры для обработки ответа
        yield from self.location_parser.parse(response)
        yield from self.info_car_parser.parse(response)
        yield from self.sprint_parser.parse(response)

    def closed(self, reason):
        # Закрываем парсеры после завершения работы
        self.location_parser.close()
        self.info_car_parser.close()
