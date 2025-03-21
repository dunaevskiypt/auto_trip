import scrapy
from scrapy.exporters import JsonItemExporter


class SalesmanSpiderSpider(scrapy.Spider):
    name = "salesman_spider"

    def __init__(self):
        self.file = open('salesman_data.json', 'wb')
        self.exporter = JsonItemExporter(self.file, ensure_ascii=False)
        self.exporter.start_exporting()

    def parse(self, response):
        # Extract data from the ad section
        ad_section = response.xpath("//section[@class='m-padding mb-20']")

        # Extract the number of car views
        views_count = ad_section.xpath(
            ".//li[@id='viewsStatistic']//span[@class='bold load']/text()").get()
        if views_count:
            views_count = views_count.strip()
        else:
            views_count = "Not specified"

        # Extract TOP information
        top_info = ad_section.xpath(
            ".//li[span[contains(text(), 'Опубліковано в ТОП')]]//span[@class='bold']/text()").get()
        if top_info:
            top_info = top_info.strip()
        else:
            top_info = "Not specified"

        # Extract the number of saves in Favorites
        saved_count = ad_section.xpath(
            ".//li[span[contains(text(), 'Наразі в Обраному')]]//span[@class='bold load']/text()").get()
        if saved_count:
            saved_count = saved_count.strip()
        else:
            saved_count = "Not specified"

        # Prepare data for export
        data = {
            "views_count": views_count,
            "top_info": top_info,
            "saved_count": saved_count
        }

        # Export data
        self.exporter.export_item(data)
        yield data

    def close(self):
        self.exporter.finish_exporting()
        self.file.close()
