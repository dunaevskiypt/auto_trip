import json
from scrapy.exporters import JsonItemExporter


class LocationParser:
    def __init__(self):
        # Відкриваємо файл для запису в бінарному режимі
        self.file = open('location_data.json', 'wb')
        # ensure_ascii=False для нормального виводу кирилиці
        self.exporter = JsonItemExporter(self.file, ensure_ascii=False)
        self.exporter.start_exporting()

    def parse(self, response):
        # Витягуємо хлібні крихти (breadcrumbs)
        breadcrumbs = response.xpath(
            "//div[@id='breadcrumbs']//div[@class='item']//a/span/text()").getall()

        # Перетворюємо всі символи Юнікоду в читабельні рядки
        readable_breadcrumbs = [breadcrumb for breadcrumb in breadcrumbs]

        # Вибираємо тільки потрібні елементи хлібних крихт: регіон (region) та місто (city)
        if len(readable_breadcrumbs) >= 4:
            # Витягуємо дані за індексами
            region = readable_breadcrumbs[2]  # Регіон
            city = readable_breadcrumbs[3]   # Місто

            # Витягуємо ID авто з елементу списку
            car_id = response.xpath(
                "//ul[@class='mb-10-list unstyle size13 mb-15']//li[contains(text(), 'ID авто')]//span[@class='bold']/text()").get()

            # Перевіряємо чи ID існує і конвертуємо його в число, якщо це необхідно
            if car_id:
                car_id = int(car_id.strip())  # Перетворюємо на ціле число
            else:
                car_id = None  # Якщо ID не знайдено, ставимо None

            # Формуємо підсумковий словник з потрібними даними
            data = {
                "region": region,
                "city": city,
                "id": car_id  # Додаємо ID авто
            }

            # Експортуємо дані у файл
            self.exporter.export_item(data)

            # Віддаємо дані у вихідний потік
            yield data

    def close(self):
        # Закриваємо файл та завершуємо експорт
        self.exporter.finish_exporting()
        self.file.close()
