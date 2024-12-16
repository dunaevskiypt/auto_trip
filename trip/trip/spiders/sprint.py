import scrapy
import re
import json
import os

fuel_translation = {
    "Бензин": "Petrol",
    "Газ": "Gas",
    "Газ пропан-бутан / Бензин": "LPG/Petrol",
    "Газ метан / Бензин": "CNG/Petrol",
    "Гібрид (HEV)": "Hybrid(HEV)",
    "Гібрид (PHEV)": "Hybrid(PHEV)",
    "Гібрид (MHEV)": "Hybrid(MHEV)",
    "Дизель": "Diesel",
    "Електро": "Electric",
}


class SprintSpider(scrapy.Spider):
    name = "sprint"
    allowed_domains = ["auto.ria.com"]
    start_urls = [
        "https://auto.ria.com/uk/search/?lang_id=4&page=0&countpage=100&category_id=1&custom=1&abroad=2"
    ]

    file_path = "/home/peter/Desktop/Parsers/autoscraper/trip/trip/data/sprintdata.json"

    def start_requests(self):
        """Инициализация: загрузка существующих данных и определение количества страниц."""
        self.existing_data = self.load_existing_data()
        self.existing_ids = {item["id"] for item in self.existing_data}

        # Запрос первой страницы для определения общего числа страниц
        url = self.start_urls[0]
        yield scrapy.Request(url, callback=self.parse_total_pages)

    def parse_total_pages(self, response):
        """Определяет общее количество страниц и запускает парсинг."""
        total_pages = response.xpath("//span[@class='page']/text()").getall()
        total_pages = max(map(int, total_pages)) if total_pages else 2800

        for page in range(total_pages):
            url = f"https://auto.ria.com/uk/search/?lang_id=4&page={page}&countpage=100&category_id=1&custom=1&abroad=2"
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        """Парсинг автомобилей с одной страницы."""
        cars = response.xpath("//section[@class='ticket-item ']")
        if not cars:
            self.logger.info(f"No cars found on page {response.url}.")
            return

        new_data = []  # Для новых данных
        for car in cars:
            # Извлечение данных автомобиля
            location = car.xpath(
                ".//li[contains(@class, 'js-location')]/text()[normalize-space()]").get()
            fuel_type_raw = car.xpath(
                ".//li[contains(@class, 'item-char') and (.//i[contains(@class, 'icon-battery') or contains(@class, 'icon-fuel')])]/text()[normalize-space()]"
            ).get()
            fuel_type = fuel_translation.get(fuel_type_raw.split(
                ",")[0].strip()) if fuel_type_raw else None
            date_added = car.xpath(
                ".//div[contains(@class, 'footer_ticket')]//span/@data-add-date").get()
            date_updated = car.xpath(
                ".//div[contains(@class, 'footer_ticket')]//span/@data-update-date").get()
            was_in_accident = car.xpath(
                ".//div[contains(@class, 'base_information')]//span[contains(text(), 'Був в ДТП')]").get() is not None
            vin = car.xpath(
                ".//span[contains(@class, 'label-vin')]/span/text()").get()
            product_url = car.xpath(
                ".//div[@class='hide']/@data-link-to-view").get()
            product_id = int(
                re.search(r"(\d+)\.html", product_url).group(1)) if product_url else None

            # Проверяем, продан ли автомобиль
            sold_block = car.xpath(
                ".//div[contains(@class, 'footer_ticket')]//span[@data-sold-date']")
            car_data = {
                "location": location.strip() if location else None,
                "fuel_type": fuel_type,
                "date_added": date_added,
                "date_updated": date_updated,
                "was_in_accident": was_in_accident,
                "vin": vin.strip() if vin else None,
                "product_url": f"https://auto.ria.com{product_url}" if product_url else None,
                "id": product_id,
                "status": "sold" if sold_block else "on_sale",
                "sold_date": sold_block.xpath("./@data-sold-date").get() if sold_block else None,
            }

            # Добавляем только новые записи
            if product_id and product_id not in self.existing_ids:
                new_data.append(car_data)
                self.existing_ids.add(product_id)

        # Обновляем данные в памяти
        self.existing_data.extend(new_data)

    def closed(self, reason):
        """Сохранение данных в файл при завершении работы."""
        self.save_data(self.existing_data)

    def load_existing_data(self):
        """Загружает существующие данные из файла."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []  # Если файл поврежден или пустой
        return []

    def save_data(self, data):
        """Сохраняет данные в файл."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
