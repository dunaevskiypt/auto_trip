import scrapy


class SprintParser(scrapy.Spider):
    name = "sprint_parser"
    allowed_domains = ["auto.ria.com"]
    start_urls = [
        "https://auto.ria.com/uk/search/?indexName=auto,order_auto,newauto_search&categories.main.id=1&country.import.usa.not=-1&price.currency=1&fuel.id[8]=6&abroad.not=0&custom.not=1&page=0&size=100"
    ]

    def parse(self, response):
        for item in response.css("section.ticket-item"):
            fuel_type, engine_capacity = self.extract_fuel_and_capacity(item)

            data = {
                "id": item.attrib.get("data-advertisement-id"),
                "fuel_type": fuel_type,  # Только название топлива
                "transmission": self.extract_text(item, "li.item-char:has(i.icon-akp)"),
                "engine_capacity": engine_capacity,  # В миллилитрах
                "date_added": item.css("span[data-add-date]::attr(data-add-date)").get(),
                "date_updated": item.css("span[data-update-date]::attr(data-update-date)").get(),
            }

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
            fuel_type = "Электрический"  # Для электромобилей указываем этот тип
            engine_capacity = None  # Для электромобилей объем двигателя не нужен
            return fuel_type, engine_capacity

    def extract_text(self, item, selector):
        """Возвращает текст внутри <li>, удаляя вложенные теги и лишние пробелы."""
        return item.css(selector).xpath("normalize-space()").get()
