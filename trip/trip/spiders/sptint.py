import scrapy
import json


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

            car_price_usd = car.xpath(
                ".//div[@class='price-ticket']//span[@data-currency='USD']/text()").get()
            car_price_uah = car.xpath(
                ".//div[@class='price-ticket']//span[@data-currency='UAH']/text()").get()

            # Обробка ціни в USD
            if car_price_usd:
                car_price_usd = car_price_usd.strip().replace("\xa0", "").replace(" ", "")
                try:
                    car_price_usd = float(car_price_usd)
                    if car_price_usd.is_integer():
                        car_price_usd = int(car_price_usd)
                except ValueError:
                    car_price_usd = None
            else:
                car_price_usd = None

            # Обробка ціни в UAH
            if car_price_uah:
                car_price_uah = car_price_uah.strip().replace("\xa0", "").replace(" ", "")
                try:
                    car_price_uah = int(car_price_uah)
                except ValueError:
                    car_price_uah = None
            else:
                car_price_uah = None

            if car_name and (car_price_usd or car_price_uah):
                car_name = car_name.strip()

                self.log(
                    f"Ціна автомобіля (USD): {car_price_usd}, Ціна автомобіля (UAH): {car_price_uah}")

                # Додаємо до списку
                cars_data.append({
                    "car_name": car_name,
                    "car_price_usd": car_price_usd,
                    "car_price_uah": car_price_uah
                })

        # Повертаємо результат для кожного автомобіля
        for car in cars_data:
            yield car
