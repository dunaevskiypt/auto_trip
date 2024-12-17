import scrapy
import re
import json
import os

# Словарь для перевода типов топлива
fuel_translation = {
    "Бензин": "Petrol",
    "Газ": "Gas",
    "Газ пропан-бутан / Бензин": "LPG/Petrol",
    "Газ метан / Бензин": "CNG/Petrol",
    "Гібрид (HEV)": "Hybrid(HEV)",
    "Гібрид (PHEV)": "Hybrid(PHEV)",
    "Гібрид (MHEV)": "Hybrid(MHEV)",
    "Дизель": "Diesel",
    "Електро": "Electric"
}


class SprintSpider(scrapy.Spider):
    name = "sprint"
    allowed_domains = ["auto.ria.com"]
    start_urls = [
        "https://auto.ria.com/uk/search/?lang_id=4&page=0&countpage=100&category_id=1&custom=1&abroad=2"
    ]
    file_path = "/data/sprintdata.json"  # Путь для хранения данных

    def start_requests(self):
        for page in range(0, 200):
            url = f"https://auto.ria.com/uk/search/?lang_id=4&page={page}&countpage=100&category_id=1&custom=1&abroad=2"
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        if not response.xpath("//section[@class='ticket-item ']"):
            self.logger.info(
                f"No cars found on page {response.url}. Stopping crawl.")
            return

        existing_data = self.load_existing_data()
        existing_ids = {item["id"]: item for item in existing_data}

        cars = response.xpath("//section[@class='ticket-item ']")
        for car in cars:
            date_added = car.xpath(
                ".//div[contains(@class, 'footer_ticket')]//span/@data-add-date").get()
            location = car.xpath(
                ".//li[contains(@class, 'js-location')]/text()[normalize-space()]").get()

            fuel_type_raw = car.xpath(
                ".//li[contains(@class, 'item-char')]/text()[normalize-space()]").get()
            fuel_type = fuel_translation.get(fuel_type_raw.split(
                ",")[0].strip(), None) if fuel_type_raw else None

            vin = car.xpath(
                ".//span[contains(@class, 'label-vin')]/span/text()").get()
            sold_block = car.xpath(
                ".//div[contains(@class, 'footer_ticket')]//span[@data-sold-date]")
            product_url = car.xpath(
                ".//div[@class='hide']/@data-link-to-view").get()

            match = re.search(r"(\d+)\.html", product_url)
            product_id = int(match.group(1)) if match else None

            car_data = {
                "location": location.strip() if location else None,
                "fuel_type": fuel_type,
                "date_added": date_added if date_added else None,
                "was_in_accident": car.xpath(".//div[contains(@class, 'base_information')]//span[contains(text(), 'Був в ДТП')]").get() is not None,
                "vin": vin.strip() if vin else None,
                "product_url": f"https://auto.ria.com{product_url}",
                "id": product_id,
                "status": "sold" if sold_block else "on_sale",
                "sold_date": sold_block.xpath("./@data-sold-date").get() if sold_block else None,
            }

            # Проверка на ID и обновление статуса
            if product_id in existing_ids:
                existing_car = existing_ids[product_id]
                if existing_car.get("status") != car_data["status"]:
                    existing_ids[product_id] = car_data  # Обновляем статус
            else:
                existing_ids[product_id] = car_data  # Добавляем новый ID

        self.save_data(list(existing_ids.values()))

    def load_existing_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def save_data(self, data):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
