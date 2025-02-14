import scrapy


class SptintSpider(scrapy.Spider):
    name = "sptint"
    allowed_domains = ["www.auto.ria.com"]
    start_urls = [
        "https://auto.ria.com/uk/legkovie/?page=1"]

    def parse(self, response):
        car_items = response.xpath("//section[@class='ticket-item ']")
        self.log(f"Знайдено {len(car_items)} автомобілів на сторінці.")

        # Список для збереження результатів
        cars_data = []

        for car in car_items:
            car_name = car.xpath(
                ".//div[@class='item ticket-title']/a/span[@class='blue bold']/text()").get()

            self.log(f"Назва автомобіля: {car_name}")

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
                    "car_location": location  # Додаємо місце продажу
                })

        # Повертаємо результат для кожного автомобіля
        for car in cars_data:
            yield car
