import scrapy


class SprintParser(scrapy.Spider):
    name = "sprint_parser"
    allowed_domains = ["auto.ria.com"]
    start_urls = [
        "https://auto.ria.com/uk/search/?lang_id=64&page=64&countpage=100&category_id=1&custom=1&abroad=2"
    ]

    def parse(self, response):
        for item in response.css("section.ticket-item"):
            fuel_type, engine_capacity = self.extract_fuel_and_capacity(item)

            # Получаем информацию о статусе и времени продажи
            sale_status, sold_time = self.get_sale_status(item)

            data = {
                "id": item.attrib.get("data-advertisement-id"),
                "fuel_type": fuel_type,  # Только название топлива
                "transmission": self.extract_text(item, "li.item-char:has(i.icon-akp)"),
                "engine_capacity": engine_capacity,  # В миллилитрах
                "date_added": item.css("span[data-add-date]::attr(data-add-date)").get(),
                "date_updated": item.css("span[data-update-date]::attr(data-update-date)").get(),
                "sale_status": sale_status,  # Статус продажи
            }

            # Добавляем время продажи, если автомобиль продан
            if sold_time:
                data["sold_time"] = sold_time

            # Добавляем top_position только если он есть
            top_position = item.css(
                "a.item.small-promote-level::attr(title)").get()
            if top_position:
                data["top_position"] = int(top_position)  # Преобразуем в число

            yield data

    def extract_fuel_and_capacity(self, item):
        """Извлекает тип топлива и объем двигателя, возвращая их отдельно."""
        fuel_text = self.extract_text(item, "li.item-char:has(i.icon-fuel)")

        if fuel_text:
            parts = fuel_text.split(", ")
            fuel_type = parts[0]  # Первое слово - это топливо
            engine_capacity = int(float(
                parts[1].split()[0]) * 1000) if len(parts) > 1 else None  # Преобразуем в мл
            return fuel_type, engine_capacity
        else:
            # Обрабатываем электромобили (если топлива нет)
            fuel_type = "Electric"  # Для электромобилей указываем этот тип
            engine_capacity = None  # Для электромобилей объем двигателя не нужен
            return fuel_type, engine_capacity

    def extract_text(self, item, selector):
        """Возвращает текст внутри <li>, удаляя вложенные теги и лишние пробелы."""
        return item.css(selector).xpath("normalize-space()").get()

    def get_sale_status(self, item):
        """Проверяет, был ли автомобиль продан и возвращает статус и время продажи."""
        sold_date = item.css(
            "span[data-sold-date]::attr(data-sold-date)").get()

        if sold_date:
            return "Sold", sold_date  # Возвращаем статус "Sold" и дату продажи
        else:
            return "For Sale", None  # Возвращаем статус "For Sale", если не продано
