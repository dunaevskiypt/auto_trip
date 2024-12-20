import scrapy
import json
import os

# Словари для перевода
color_translation = {
    "Бежевий": "Beige", "Чорний": "Black", "Синій": "Blue", "Коричневий": "Brown",
    "Зелений": "Green", "Сірий": "Gray", "Помаранчевий": "Orange",
    "Фіолетовий": "Purple", "Червоний": "Red", "Білий": "White", "Жовтий": "Yellow"
}

gearbox_translation = {
    "Ручна / Механіка": "Manual", "Автомат": "Automatic",
    "Типтронік": "Tiptronic", "Робот": "Robot", "Варіатор": "CVT"
}

drive_translation = {
    "Повний": "All-Wheel Drive", "Передній": "Front-Wheel Drive", "Задній": "Rear-Wheel Drive"
}


class ExtractorSpider(scrapy.Spider):
    name = "extractor"
    allowed_domains = ["auto.ria.com"]

    # Пути для файлов (обновленные для Docker Volume)
    sprintdata_file_path = "/data/sprintdata.json"
    file_path = "/data/exdata.json"

    def start_requests(self):
        # Загрузка уникальных ID из файла для проверки
        existing_ids = self.load_existing_ids()

        # Загрузка данных из sprintdata.json
        if not os.path.exists(self.sprintdata_file_path):
            self.logger.error(f"Файл {self.sprintdata_file_path} не найден.")
            return

        with open(self.sprintdata_file_path, 'r', encoding='utf-8') as f:
            try:
                sprint_data = json.load(f)
            except json.JSONDecodeError:
                self.logger.error("Ошибка чтения JSON из sprintdata.json")
                return

        for car_entry in sprint_data:
            car_id = car_entry.get("id")
            product_url = car_entry.get("product_url")
            # Проверяем, есть ли ID в уже обработанных
            if product_url and car_id not in existing_ids:
                yield scrapy.Request(product_url, callback=self.parse_car)

    def parse_car(self, response):
        self.logger.info(f"Парсинг автомобиля: {response.url}")
        car_data = {
            "brand": None, "model": None, "year": None, "price_usd": None,
            "mileage": None, "state_number": None, "owners_count": None, "color": None,
            "gearbox": None, "drive": None, "id": None,
        }

        try:
            car_title = response.css("h1.head::attr(title)").get()
            if car_title:
                title_parts = car_title.split()
                car_data["brand"] = title_parts[0]
                car_data["model"] = " ".join(
                    title_parts[1:-1]) if title_parts[-1].isdigit() else " ".join(title_parts[1:])
                car_data["year"] = title_parts[-1] if title_parts[-1].isdigit() else None

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
            car_data["owners_count"] = self.extract_optional_data(
                response, "Кількість власників", default_value=None)
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

            self.save_to_json(car_data)
            yield car_data
        except Exception as e:
            self.logger.error(f"Ошибка парсинга {response.url}: {e}")

    def load_existing_ids(self):
        """Загружает уникальные ID из exdata.json для проверки."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                try:
                    return set(item["id"] for item in json.load(f) if "id" in item)
                except json.JSONDecodeError:
                    self.logger.error("Ошибка чтения JSON из exdata.json")
        return set()

    def save_to_json(self, data):
        """Сохраняет новую запись в exdata.json, избегая дубликатов."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = {
                        item["id"]: item for item in json.load(f) if "id" in item}
                except json.JSONDecodeError:
                    existing_data = {}
        else:
            existing_data = {}

        # Проверяем уникальность ID
        if data["id"] not in existing_data:
            existing_data[data["id"]] = data
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(list(existing_data.values()),
                          f, ensure_ascii=False, indent=4)

    def extract_optional_data(self, response, field_name, default_value=None, translation=None):
        data = response.css(
            f"dd:contains('{field_name}') .argument::text").get()
        if data:
            data = data.strip()
            if field_name == "Колір" and "металік" in data.lower():
                color_base = data.split()[0]
                return f"{translation.get(color_base, color_base)} Metallic" if translation else color_base
            return translation.get(data, data) if translation else data
        return default_value
