import scrapy
import json
import os
import re

# Словари для перевода
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


class CombinedSpider(scrapy.Spider):
    name = "combined"
    allowed_domains = ["auto.ria.com"]

    # Генерация URL для 2900 страниц
    start_urls = [
        f"https://auto.ria.com/uk/search/?lang_id=4&page={page}&countpage=100&category_id=1&custom=1&abroad=2"
        for page in range(2900)
    ]

    # Путь к файлу данных
    data_file_path = "/home/peter/Desktop/Parsers/autoscraper/trip/trip/data/auto_data.json"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Проверяем, существует ли файл, если нет — создаем
        if not os.path.exists(self.data_file_path):
            with open(self.data_file_path, 'w', encoding='utf-8') as f:
                f.write("")

    def parse(self, response):
        cars = response.xpath("//section[@class='ticket-item ']")
        for car in cars:
            product_url = car.xpath(
                ".//div[@class='hide']/@data-link-to-view").get()
            if product_url:
                product_url = f"https://auto.ria.com{product_url}"
                sprint_data = {
                    "location": car.xpath(".//li[contains(@class, 'js-location')]/text()[normalize-space()]").get(),
                    "fuel_type": self.get_fuel_type(car),
                    "date_added": car.xpath(".//span/@data-add-date").get(),
                    "date_updated": car.xpath(".//span/@data-update-date").get(),
                    "was_in_accident": bool(car.xpath(".//span[contains(text(), 'Був в ДТП')]").get()),
                    "vin": car.xpath(".//span[contains(@class, 'label-vin')]/span/text()").get(),
                    "product_url": product_url,
                    "id": self.extract_id_from_url(product_url),
                    "status": "sold" if car.xpath(".//span[@data-sold-date]").get() else "on_sale"
                }
                yield scrapy.Request(product_url, callback=self.parse_car, meta={"sprint_data": sprint_data})

    def parse_car(self, response):
        sprint_data = response.meta["sprint_data"]
        extractor_data = {
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
            "id": None
        }

        try:
            car_title = response.css("h1.head::attr(title)").get()
            if car_title:
                title_parts = car_title.split()
                if len(title_parts) > 2 and title_parts[-1].isdigit():
                    extractor_data["brand"] = title_parts[0]
                    extractor_data["model"] = " ".join(title_parts[1:-1])
                    extractor_data["year"] = title_parts[-1]
                else:
                    extractor_data["brand"] = title_parts[0]
                    extractor_data["model"] = " ".join(title_parts[1:])

            price_usd = response.css("div.price_value strong::text").get()
            if price_usd:
                extractor_data["price_usd"] = int(
                    price_usd.strip().replace(" ", "").replace("$", ""))

            mileage = response.css(
                "div.base-information span.size18::text").get()
            if mileage:
                extractor_data["mileage"] = int(
                    mileage.strip().replace(" ", "").replace("км", "")) * 1000

            extractor_data["state_number"] = response.css(
                "span.state-num.ua::text").get()
            extractor_data["seller_name"] = response.css(
                "div.seller_info_name a::text").get()

            owners_count = self.extract_optional_data(
                response, "Кількість власників")
            if owners_count and owners_count.isdigit():
                extractor_data["owners_count"] = int(owners_count)

            extractor_data["color"] = self.extract_optional_data(
                response, "Колір", translation=color_translation)
            extractor_data["gearbox"] = self.extract_optional_data(
                response, "Коробка передач", translation=gearbox_translation)
            extractor_data["drive"] = self.extract_optional_data(
                response, "Привід", translation=drive_translation)

            car_id = response.css(
                "ul.mb-10-list li:contains('ID авто') span.bold::text").get()
            if car_id:
                extractor_data["id"] = int(car_id.strip())

            combined_data = {**sprint_data, **extractor_data}
            self.save_to_file(combined_data)
            yield combined_data

        except Exception as e:
            self.logger.error(f"Error parsing car details: {e}")

    def save_to_file(self, data):
        """Saves the scraped data to a JSON file."""

        # Check if the data file exists
        if os.path.exists(self.data_file_path):
            # Load existing data (handle potential JSON decode errors)
            try:
                with open(self.data_file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []

        else:
            # Create an empty list if the file doesn't exist
            existing_data = []

        # Append the new data to the existing list
        existing_data.append(data)

        # Open the file in write mode and ensure proper encoding
        with open(self.data_file_path, 'w', encoding='utf-8') as f:
            # Write the updated data with indentation for readability
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

    def get_fuel_type(self, car):
        fuel_type_raw = car.xpath(
            ".//li[contains(@class, 'item-char') and .//i[contains(@class, 'icon-battery') or contains(@class, 'icon-fuel')]]/text()[normalize-space()]"
        ).get()
        if fuel_type_raw:
            fuel_type = fuel_type_raw.split(",")[0].strip()
            return fuel_translation.get(fuel_type, None)
        return None

    def extract_id_from_url(self, url):
        match = re.search(r"(\d+)\.html", url)
        return int(match.group(1)) if match else None

    def extract_optional_data(self, response, field_name, translation=None):
        data = response.css(
            f"dd:contains('{field_name}') .argument::text").get()
        if data:
            data = data.strip()
            if field_name == "Колір" and "металік" in data.lower():
                color_base = data.split()[0]
                color_translated = translation.get(color_base, None)
                return f"{color_translated} Metallic" if color_translated else data
            if translation:
                return translation.get(data, None)
            return data
        return None
