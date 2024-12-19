import scrapy
import re  # Для работы с регулярными выражениями
import json  # Для работы с сохранением данных в JSON

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
    parse_counter = 1  # Инициализация счетчика парсинга
    all_cars_data = []  # Список для хранения всех данных
    existing_ids = set()  # Множество для хранения ID уже обработанных автомобилей

    def start_requests(self):
        # Делаем запросы на страницы от 0 до 2879
        for page in range(0, 100):
            url = f"https://auto.ria.com/uk/search/?lang_id=4&page={page}&countpage=100&category_id=1&custom=1&abroad=2"
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # Проверка наличия контента на странице
        if not response.xpath("//section[@class='ticket-item ']"):
            self.logger.info(
                f"No cars found on page {response.url}. Stopping crawl.")
            return  # Прерываем выполнение, если контент не найден
        # Обрабатываем найденные автомобили на странице
        cars = response.xpath("//section[@class='ticket-item ']")
        for car in cars:
            # Дата подачи
            date_added = car.xpath(
                ".//div[contains(@class, 'footer_ticket')]//span/@data-add-date"
            ).get()
            # Дата обновления
            date_updated = car.xpath(
                ".//div[contains(@class, 'footer_ticket')]//span/@data-update-date"
            ).get()
            # Проверка на факт ДТП
            was_in_accident = car.xpath(
                ".//div[contains(@class, 'base_information')]//span[contains(text(), 'Був в ДТП')]"
            ).get() is not None  # Если элемент найден, возвращаем True, иначе False
            # Прочие данные: город и тип топлива
            location = car.xpath(
                ".//li[contains(@class, 'js-location')]/text()[normalize-space()]"
            ).get()
            fuel_type_raw = car.xpath(
                ".//li[contains(@class, 'item-char') and .//i[contains(@class, 'icon-battery') or contains(@class, 'icon-fuel')]]/text()[normalize-space()]"
            ).get()
            # Извлечение только типа топлива (удаление лишних данных после запятой, например, литраж)
            if fuel_type_raw:
                fuel_type = fuel_type_raw.split(",")[0].strip()
                # Переводим тип топлива на английский
                # Если не нашли в словаре, оставляем null
                fuel_type = fuel_translation.get(fuel_type, None)
            else:
                fuel_type = None  # null, если не указано
            # VIN-код
            vin = car.xpath(
                ".//span[contains(@class, 'label-vin')]/span/text()"
            ).get()
            # Блок с информацией о статусе продажи
            sold_block = car.xpath(
                ".//div[contains(@class, 'footer_ticket')]//span[@data-sold-date]"
            )
            # Извлечение ссылки на страницу товара
            product_url = car.xpath(
                ".//div[@class='hide']/@data-link-to-view"
            ).get()
            # Извлечение ID из ссылки
            match = re.search(r"(\d+)\.html", product_url)
            if match:
                product_id = int(match.group(1))  # Преобразуем в целое число
            else:
                product_id = None  # Если ID не найден
            # Если автомобиль продан
            car_data = {
                "location": location.strip() if location else None,
                "fuel_type": fuel_type,
                "date_added": date_added if date_added else None,
                "date_updated": date_updated if date_updated else None,
                "was_in_accident": was_in_accident,
                "vin": vin.strip() if vin else None,
                "product_url": f"https://auto.ria.com{product_url}",
                "id": product_id,  # Добавляем ID
            }
            if sold_block:
                sold_date = sold_block.xpath("./@data-sold-date").get()
                car_data["status"] = "sold"
                car_data["sold_date"] = sold_date if sold_date else None
            else:
                # Автомобиль в продаже
                car_data["status"] = "on_sale"

            # Если ID уже существует в обработанных данных, проверяем статус
            if product_id in self.existing_ids:
                # Если статус стал "sold", обновляем только его
                for existing_car in self.all_cars_data:
                    if existing_car["id"] == product_id:
                        if existing_car["status"] != "sold" and car_data["status"] == "sold":
                            existing_car["status"] = "sold"
                            existing_car["sold_date"] = car_data["sold_date"]
                            break
            else:
                # Если ID новый, добавляем его в список
                self.existing_ids.add(product_id)
                self.all_cars_data.append(car_data)

    def closed(self, reason):
        # Этот метод вызывается при завершении работы паука
        file_path = "/data/sprintdata.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            # Записываем данные в файл в формате JSON-массив
            json.dump(self.all_cars_data, f, ensure_ascii=False, indent=4)
