import scrapy
from datetime import datetime


class SptintSpider(scrapy.Spider):
    name = "sptint"
    allowed_domains = ["auto.ria.com"]

    # Налаштовуємо start_urls на порожній список
    start_urls = []

    def start_requests(self):
        # Генеруємо URL для кожної сторінки від 0 до 3000 з кроком 100
        for page in range(0, 1000):  # Створюємо сторінки від 0 до 3000 з кроком 100
            url = f"https://auto.ria.com/uk/search/?lang_id=4&page={page}&countpage=100&category_id=1&custom=1&abroad=2"
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        car_items = response.xpath("//section[@class='ticket-item ']")
        self.log(f"Знайдено {len(car_items)} автомобілів на сторінці.")

        # Список для збереження результатів
        cars_data = []

        for car in car_items:
            car_name = car.xpath(
                ".//div[@class='item ticket-title']/a/span[@class='blue bold']/text()").get()

            self.log(f"Назва автомобіля: {car_name}")

            # Отримуємо посилання на автомобіль
            car_link = car.xpath(".//a[@class='m-link-ticket']/@href").get()
            if car_link:
                # Виділяємо ID з посилання
                car_id = car_link.split('_')[-1].split('.')[0]
            else:
                car_id = None

            self.log(
                f"Посилання на автомобіль: {car_link}, ID автомобіля: {car_id}")

            # Отримуємо ціну в USD
            car_price_usd = car.xpath(
                ".//div[@class='price-ticket']//span[@data-currency='USD']/text()").get()
            car_price_uah = car.xpath(
                ".//div[@class='price-ticket']//span[@data-currency='UAH']/text()").get()

            # Нормалізація ціни
            if car_price_usd:
                car_price_usd = car_price_usd.strip().replace("\xa0", "").replace(" ", "")
                try:
                    car_price_usd = float(car_price_usd)
                except ValueError:
                    car_price_usd = None
            else:
                car_price_usd = None

            if car_price_uah:
                car_price_uah = car_price_uah.strip().replace("\xa0", "").replace(" ", "")
                try:
                    car_price_uah = int(car_price_uah)
                except ValueError:
                    car_price_uah = None
            else:
                car_price_uah = None

            # Витягуємо місце продажу (місто)
            location = car.xpath(
                ".//li[contains(@class, 'js-location')]//text()").getall()
            location = " ".join([loc.strip()
                                 for loc in location if loc.strip()])

            # Очищаємо локацію від зайвих текстів
            if location:
                location = location.replace(" ( від )", "").strip()

            self.log(f"Місце продажу: {location}")

            # Витягуємо пробіг
            mileage = car.xpath(
                ".//li[contains(@class, 'item-char js-race')]//text()").get()
            if mileage:
                mileage = mileage.strip().replace(" тис. км", "").replace(" ", "")
                try:
                    mileage = int(float(mileage) * 1000)
                except ValueError:
                    mileage = None
            else:
                mileage = None

            # Витягуємо тип палива
            fuel_type = car.xpath(
                ".//li[contains(@class, 'item-char')]//i[@class='icon-fuel']/following-sibling::text()").get()
            if fuel_type:
                fuel_type = fuel_type.strip().split(
                    ',')[0]  # Беремо тільки тип палива

            # Витягуємо об'єм двигуна
            engine_volume = car.xpath(
                ".//li[contains(@class, 'item-char')]//i[@class='icon-fuel']/following-sibling::text()").get()
            if engine_volume:
                engine_volume = engine_volume.split(',')[1].strip(
                ) if ',' in engine_volume else engine_volume.strip()
                engine_volume = engine_volume.replace(" л.", "").replace(
                    " ", "")  # Видаляємо " л." та пробіли
                try:
                    # Перетворюємо на число
                    engine_volume = int(float(engine_volume) * 1000)
                except ValueError:
                    engine_volume = None

            # Витягуємо тип коробки передач за title
            transmission_type = car.xpath(
                ".//li[contains(@class, 'item-char')]//i[@title='Тип коробки передач']/following-sibling::text()").get()

            # Якщо не знайдено, встановлюємо значення "Невідомо"
            if not transmission_type:
                transmission_type = "None"

            # Очищаємо тип коробки передач від пробілів
            transmission_type = transmission_type.strip()

            # Витягуємо VIN-код
            vin_code = car.xpath(
                ".//span[@class='label-vin']/span/text()").get()
            if vin_code:
                vin_code = vin_code.strip()
            else:
                vin_code = None

            # Витягуємо статус ДТП
            accident_status = car.xpath(
                ".//span[contains(@class, 'state')]/text()").get()
            if accident_status and 'ДТП' in accident_status:
                accident_status = "YES"
            else:
                accident_status = "NO"

            # Витягуємо дату додавання оголошення
            add_date_str = car.xpath(
                ".//span[@data-add-date]").attrib.get("data-add-date")
            if add_date_str:
                try:
                    add_date = datetime.strptime(
                        add_date_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    add_date = None
            else:
                add_date = None

            self.log(
                f"Тип палива: {fuel_type}, Об'єм двигуна: {engine_volume}, Тип трансмісії: {transmission_type}, Статус ДТП: {accident_status}, Дата додавання оголошення: {add_date}")

            if car_name and (car_price_usd or car_price_uah) and mileage is not None:
                car_name = car_name.strip()

                self.log(
                    f"Ціна автомобіля (USD): {car_price_usd}, Ціна автомобіля (UAH): {car_price_uah}, Пробіг: {mileage} км")

                # Додаємо до списку
                cars_data.append({
                    "car_name": car_name,
                    "car_price_usd": car_price_usd,
                    "car_price_uah": car_price_uah,
                    "car_mileage": mileage,
                    "car_location": location,
                    "fuel_type": fuel_type,  # Додаємо тип палива
                    "engine_volume": engine_volume,  # Додаємо об'єм двигуна
                    "transmission_type": transmission_type,  # Додаємо тип трансмісії
                    "vin_code": vin_code,  # Додаємо VIN-код
                    "accident_status": accident_status,  # Додаємо статус ДТП
                    "add_date": add_date,  # Додаємо дату додавання
                    "car_link": car_link,  # Додаємо посилання
                    "car_id": car_id  # Додаємо ID автомобіля
                })

        # Повертаємо результат для кожного автомобіля
        for car in cars_data:
            yield car
