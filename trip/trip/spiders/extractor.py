import scrapy
import time
import json  # Для работы с сохранением данных в JSON
import os  # Для работы с файлами

# Словари для перевода
color_translation = {
    "Бежевий": "Beige",
    "Чорний": "Black",
    "Синій": "Blue",
    "Коричневий": "Brown",
    "Зелений": "Green",
    "Сірий": "Gray",
    "Помаранчевий": "Orange",
    "Фіолетовий": "Purple",
    "Червоний": "Red",
    "Білий": "White",
    "Жовтий": "Yellow"
}

gearbox_translation = {
    "Ручна / Механіка": "Manual",
    "Автомат": "Automatic",
    "Типтронік": "Tiptronic",
    "Робот": "Robot",
    "Варіатор": "CVT"
}

drive_translation = {
    "Повний": "All-Wheel Drive",
    "Передній": "Front-Wheel Drive",
    "Задній": "Rear-Wheel Drive"
}


class ExtractorSpider(scrapy.Spider):
    name = "extractor"
    allowed_domains = ["auto.ria.com"]

    # Настройки
    total_pages = 20  # Общее количество страниц
    pause_interval = 50  # Сколько страниц парсить перед паузой
    pause_duration = 20  # Длительность паузы в секундах

    # Путь к файлу для сохранения данных
    file_path = "/home/peter/Desktop/Parsers/autoscraper/trip/trip/data/exdata.json"

    def start_requests(self):
        for page in range(self.total_pages):
            url = f"https://auto.ria.com/uk/search/?lang_id=4&page={page}&countpage=100&category_id=1&custom=1&abroad=2"
            yield scrapy.Request(
                url, callback=self.parse, meta={"page_number": page}
            )

    def parse(self, response):
        page_number = response.meta.get("page_number")
        self.logger.info(
            f"Парсинг сторінки: {response.url} (сторінка {page_number + 1})")

        # Сбор ссылок на автомобили
        car_links = response.css(
            "div.content-bar a.m-link-ticket::attr(href)").getall()
        for link in car_links:
            yield response.follow(link, callback=self.parse_car)

        # Пауза после каждых `pause_interval` страниц
        if (page_number + 1) % self.pause_interval == 0:
            self.logger.info(
                f"Пауза на {self.pause_duration} секунд после {page_number + 1} страниц")
            time.sleep(self.pause_duration)

    def parse_car(self, response):
        self.logger.info(f"Парсинг автомобіля: {response.url}")
        car_data = {
            "brand": None,
            "model": None,
            "year": None,
            "price_usd": None,
            "mileage": None,
            "state_number": None,
            "seller_name": None,
            "owners_count": None,
            "color": None,
            "gearbox": None,
            "drive": None,
            "id": None,
        }

        try:
            car_title = response.css("h1.head::attr(title)").get()
            if car_title:
                title_parts = car_title.split()
                if len(title_parts) > 2 and title_parts[-1].isdigit():
                    car_data["brand"] = title_parts[0]
                    car_data["model"] = " ".join(title_parts[1:-1])
                    car_data["year"] = title_parts[-1]
                else:
                    car_data["brand"] = title_parts[0]
                    car_data["model"] = " ".join(title_parts[1:])
            price_usd = response.css("div.price_value strong::text").get()
            if price_usd:
                car_data["price_usd"] = int(
                    price_usd.strip().replace(" ", "").replace("$", ""))
            mileage = response.css(
                "div.base-information span.size18::text").get()
            if mileage:
                car_data["mileage"] = int(mileage.strip().replace(
                    " ", "").replace("км", "")) * 1000
            state_number = response.css("span.state-num.ua::text").get()
            if state_number:
                car_data["state_number"] = state_number.strip().replace(" ", "")
            car_data["seller_name"] = response.css(
                "div.seller_info_name a::text").get()
            owners_count = self.extract_optional_data(
                response, "Кількість власників")
            if owners_count and owners_count.isdigit():
                car_data["owners_count"] = int(owners_count)
            car_data["color"] = self.extract_optional_data(
                response, "Колір", translation=color_translation)
            car_data["gearbox"] = self.extract_optional_data(
                response, "Коробка передач", translation=gearbox_translation)
            car_data["drive"] = self.extract_optional_data(
                response, "Привід", translation=drive_translation)
            car_id = response.css(
                "ul.mb-10-list li:contains('ID авто') span.bold::text").get()
            if car_id:
                car_data["id"] = int(car_id.strip())

            # Сохранение данных в файл
            self.save_to_json(car_data)

            yield car_data
        except Exception as e:
            self.logger.error(
                f"Помилка при парсингу сторінки {response.url}: {e}")

    def save_to_json(self, data):
        # Проверяем, существует ли файл
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []

        # Проверяем, есть ли уже такая запись
        if not any(item["id"] == data["id"] for item in existing_data):
            existing_data.append(data)

            # Сохраняем данные в файл
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)

    def extract_optional_data(self, response, field_name, default_value=None, translation=None):
        data = response.css(
            f"dd:contains('{field_name}') .argument::text").get()
        if data:
            data = data.strip()
            # Проверка на наличие слова "металік" в цвете
            if field_name == "Колір" and "металік" in data.lower():
                color_base = data.split()[0]  # Берем основную часть цвета
                color_translated = translation.get(color_base, None)
                if color_translated:
                    return f"{color_translated} Metallic"
            # Применяем перевод, если словарь задан
            if translation:
                return translation.get(data, None)
            return data
        return default_value
