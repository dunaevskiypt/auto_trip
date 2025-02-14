import scrapy
from datetime import datetime
import re


class SptintSpider(scrapy.Spider):
    name = "sptint"
    allowed_domains = ["auto.ria.com"]

    start_urls = []

    def start_requests(self):
        for page in range(0, 10):  # Replace 10 with the desired number of pages
            url = f"https://auto.ria.com/uk/search/?lang_id=4&page={page}&countpage=100&category_id=1&custom=1&abroad=2"
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        car_items = response.xpath("//section[@class='ticket-item ']")
        self.log(f"Found {len(car_items)} cars on the page.")

        cars_data = []

        for car in car_items:
            car_name = car.xpath(
                ".//div[@class='item ticket-title']/a/span[@class='blue bold']/text()"
            ).get()

            car_link = car.xpath(".//a[@class='m-link-ticket']/@href").get()
            if car_link:
                car_id = car_link.split('_')[-1].split('.')[0]
            else:
                car_id = None

            car_price_usd = car.xpath(
                ".//div[@class='price-ticket']//span[@data-currency='USD']/text()"
            ).get()
            car_price_uah = car.xpath(
                ".//div[@class='price-ticket']//span[@data-currency='UAH']/text()"
            ).get()

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

            location = car.xpath(
                ".//li[contains(@class, 'js-location')]//text()"
            ).getall()
            location = " ".join([loc.strip()
                                for loc in location if loc.strip()])
            if location:
                location = location.replace(" ( від )", "").strip()

            mileage = car.xpath(
                ".//li[contains(@class, 'item-char js-race')]//text()"
            ).get()
            if mileage:
                mileage = mileage.strip().replace(" тис. км", "").replace(" ", "")
                try:
                    mileage = int(float(mileage) * 1000)
                except ValueError:
                    mileage = None
            else:
                mileage = None

            fuel_type = car.xpath(
                ".//li[contains(@class, 'item-char')]//i[@class='icon-fuel']/following-sibling::text()"
            ).get()
            if fuel_type:
                fuel_type = fuel_type.strip().split(',')[0]

            engine_volume = car.xpath(
                ".//li[contains(@class, 'item-char')]//i[@class='icon-fuel']/following-sibling::text()"
            ).get()
            if engine_volume:
                engine_volume = engine_volume.split(',')[1].strip(
                ) if ',' in engine_volume else engine_volume.strip()
                engine_volume = engine_volume.replace(
                    " л.", "").replace(" ", "")
                try:
                    engine_volume = int(float(engine_volume) * 1000)
                except ValueError:
                    engine_volume = None

            transmission_type = car.xpath(
                ".//li[contains(@class, 'item-char')]//i[@title='Тип коробки передач']/following-sibling::text()"
            ).get()
            if not transmission_type:
                transmission_type = "None"
            transmission_type = transmission_type.strip()

            vin_code = car.xpath(
                ".//span[@class='label-vin']/span/text()"
            ).get()
            if vin_code:
                vin_code = vin_code.strip()
            else:
                vin_code = None

            accident_status = car.xpath(
                ".//span[contains(@class, 'state')]/text()"
            ).get()
            if accident_status and 'ДТП' in accident_status:
                accident_status = "YES"
            else:
                accident_status = "NO"

            add_date_str = car.xpath(
                ".//span[@data-add-date]").attrib.get("data-add-date")
            if add_date_str:
                try:
                    add_date = datetime.strptime(
                        add_date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")  # Only date, no time
                except ValueError:
                    add_date = None
            else:
                add_date = None

            sold_element = car.xpath(".//span[@data-sold-date]")
            if sold_element:
                sold_date_str = sold_element.attrib.get("data-sold-date")
                try:
                    sold_date = datetime.strptime(
                        sold_date_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    sold_date = None
                sale_status = "sold"
            else:
                sold_date = None
                sale_status = "for sale"

            # --- Extracting car_name, model and year ---
            if car_name:
                # Split car name into brand and model
                name_parts = car_name.strip().split(' ', 1)
                car_name = name_parts[0]  # First part is the brand
                model = name_parts[1] if len(
                    name_parts) > 1 else None  # Rest is the model
            else:
                car_name, model = None, None

            # Extract the year of the car from the title attribute or year in the link
            car_year = car.xpath(".//a[@class='address']/@title").get()
            if car_year:
                # Match a 4-digit number
                match = re.search(r'(\d{4})', car_year)
                if match:
                    car_year = match.group(1)
                else:
                    car_year = None
            else:
                car_year = None

            self.log(
                f"Fuel type: {fuel_type}, Engine volume: {engine_volume}, Transmission type: {transmission_type}, "
                f"Accident status: {accident_status}, Added date: {add_date}, Sale status: {sale_status}"
            )

            if car_name and (car_price_usd or car_price_uah) and mileage is not None:
                self.log(
                    f"Price (USD): {car_price_usd}, Price (UAH): {car_price_uah}, Mileage: {mileage} km"
                )

                cars_data.append({
                    "car_name": car_name,  # Only brand name here
                    "model": model,         # Model
                    "car_price_usd": car_price_usd,
                    "car_price_uah": car_price_uah,
                    "car_mileage": mileage,
                    "car_location": location,
                    "fuel_type": fuel_type,
                    "engine_volume": engine_volume,
                    "transmission_type": transmission_type,
                    "vin_code": vin_code,
                    "accident_status": accident_status,
                    "add_date": add_date,  # Only date, no time
                    "car_link": car_link,
                    "car_id": car_id,
                    "sale_status": sale_status,      # "sold" or "for sale"
                    "sold_date": sold_date,          # Sold date if available
                    "car_year": car_year             # Year extracted from link or title
                })

        for car in cars_data:
            yield car
