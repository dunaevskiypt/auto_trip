import json
from scrapy.exporters import JsonItemExporter
import re


class InfoCarParser:
    def __init__(self):
        self.file = open('car_info_data.json', 'wb')
        self.exporter = JsonItemExporter(self.file, ensure_ascii=False)
        self.exporter.start_exporting()

    def parse(self, response):
        heading = response.xpath("//div[@class='heading']")
        brand_model = heading.xpath(".//h1[@class='head']/text()").get()

        if brand_model:
            brand_model_parts = brand_model.strip().split(" ", 1)
            if len(brand_model_parts) > 1:
                brand = brand_model_parts[0]
                model = brand_model_parts[1]
            else:
                brand = brand_model_parts[0]
                model = ""

            # Перевірка на наявність року у моделі
            year_match = re.search(r"(\d{4})", model)
            if year_match:
                year = year_match.group(1)
                model = model.replace(year, '').strip()
            else:
                year = None

        price_section = response.xpath("//section[@class='price mb-15 mhide']")
        price_value = price_section.xpath(
            ".//div[@class='price_value']//strong/text()").get()
        if price_value:
            price = re.sub(r"[^\d]", "", price_value.strip())

        mileage_section = response.xpath(
            "//section[@class='price mb-15 mhide']//div[contains(@class, 'base-information')]")
        mileage_value = mileage_section.xpath(
            ".//span[@class='size18']/text()").get()
        if mileage_value:
            mileage = re.sub(r"[^\d]", "", mileage_value.strip())
            # множимо на 1000, щоб отримати пробіг в км
            mileage = int(mileage) * 100

        # Витягування кількості власників
        owners_section = response.xpath(
            "//dd[span[contains(text(), 'Кількість власників')]]")
        owners_value = owners_section.xpath(
            ".//span[@class='argument']/text()").get()
        if owners_value:
            owners = int(owners_value.strip())
        else:
            owners = None  # Якщо кількість власників не вказана, ставимо null

        # Витягування VIN-коду
        vin_code = response.xpath("//span[@class='label-vin']/text()").get()
        if vin_code:
            vin_code = vin_code.strip()
        else:
            vin_code = None  # Якщо VIN-код не вказаний, ставимо null

        # Витягування державного номера
        state_number = response.xpath(
            "//span[@class='state-num ua']/text()").get()
        if state_number:
            state_number = state_number.strip()
            # Видаляємо всі пробіли
            state_number = re.sub(r"\s+", "", state_number)
        else:
            state_number = None  # Якщо державний номер не вказаний, ставимо null

        data = {
            "brand": brand,
            "model": model,
            "year": year,
            "price": int(price) if price else None,
            "mileage": int(mileage) if mileage else None,
            "owners": owners,  # Додаємо кількість власників
            "vin_code": vin_code,  # Додаємо VIN-код
            "state_number": state_number  # Додаємо державний номер
        }

        self.exporter.export_item(data)
        yield data

    def close(self):
        self.exporter.finish_exporting()
        self.file.close()
