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

        # Перевірка наявності brand та model
        if brand_model:
            brand_model_parts = brand_model.strip().split(" ", 1)
            if len(brand_model_parts) > 1:
                brand = brand_model_parts[0]
                model = brand_model_parts[1]
            else:
                brand = brand_model_parts[0]
                model = ""
        else:
            brand = None
            model = None

        # Витягування року, якщо він є в моделі
        year = None
        if model:
            year_match = re.search(r"(\d{4})", model)
            if year_match:
                year = year_match.group(1)
                model = model.replace(year, '').strip()

        # Витягування ID авто
        car_id = response.xpath(
            "//ul[@class='mb-10-list unstyle size13 mb-15']//li[@id='addDate']/following-sibling::li[@class='item grey']//span[@class='bold']/text()").get()

        # Перетворення car_id на ціле число (якщо воно є)
        if car_id:
            car_id = int(car_id.strip())  # Перетворюємо на ціле число
        else:
            car_id = None  # Якщо car_id відсутнє, ставимо None

        # Витягування ціни
        price_section = response.xpath("//section[@class='price mb-15 mhide']")
        price_value = price_section.xpath(
            ".//div[@class='price_value']//strong/text()").get()
        price = None
        if price_value:
            price = re.sub(r"[^\d]", "", price_value.strip())
            price = int(price) if price else None

        # Витягування пробігу
        mileage_section = response.xpath(
            "//section[@class='price mb-15 mhide']//div[contains(@class, 'base-information')]")
        mileage_value = mileage_section.xpath(
            ".//span[@class='size18']/text()").get()
        mileage = None
        if mileage_value:
            mileage = re.sub(r"[^\d]", "", mileage_value.strip())
            # Припускаємо, що пробіг в милях, конвертуємо в кілометри
            mileage = int(mileage) * 100

        # Витягування кількості власників
        owners_section = response.xpath(
            "//dd[span[contains(text(), 'Кількість власників')]]")
        owners_value = owners_section.xpath(
            ".//span[@class='argument']/text()").get()
        owners = None
        if owners_value:
            owners = int(owners_value.strip())

        # Витягування VIN коду
        vin_code = response.xpath("//span[@class='label-vin']/text()").get()
        if vin_code:
            vin_code = vin_code.strip()
        else:
            vin_code = None

        # Витягування державного номера
        state_number = response.xpath(
            "//span[@class='state-num ua']/text()").get()
        if state_number:
            state_number = re.sub(r"\s+", "", state_number.strip())
        else:
            state_number = None

        # Формування даних для експорту
        data = {
            "brand": brand,
            "model": model,
            "year": year,
            "price": price,
            "mileage": mileage,
            "owners": owners,
            "vin_code": vin_code,
            "state_number": state_number,
            "car_id": car_id  # Тепер car_id є числом
        }

        # Експортуємо дані
        self.exporter.export_item(data)
        yield data

    def close(self):
        self.exporter.finish_exporting()
        self.file.close()
