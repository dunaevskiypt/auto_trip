import scrapy


class SprintParser(scrapy.Spider):
    name = "sprint_parser"
    allowed_domains = ["auto.ria.com"]
    start_urls = [
        "https://auto.ria.com/uk/search/?lang_id=4&page=0&countpage=100&category_id=1&custom=1&abroad=2"
    ]

    def parse(self, response):
        # Parse the current page
        for item in response.css("section.ticket-item"):
            fuel_type, engine_capacity = self.extract_fuel_and_capacity(item)

            # Get sale status and sold time
            sale_status, sold_time = self.get_sale_status(item)

            # Add accident information
            accident_info = self.check_accident(item)

            # Extract additional information from <a class="item small-promote-level">
            promotion_level = self.extract_promotion_level(item)

            data = {
                "id": item.attrib.get("data-advertisement-id"),
                "fuel_type": fuel_type,  # Fuel type only
                "transmission": self.extract_text(item, "li.item-char:has(i.icon-akp)"),
                "engine_capacity": engine_capacity,  # In milliliters
                "date_added": item.css("span[data-add-date]::attr(data-add-date)").get(),
                "date_updated": item.css("span[data-update-date]::attr(data-update-date)").get(),
                "sale_status": sale_status,  # Sale status
                "accident": accident_info,  # Accident information
                "promotion_level": promotion_level,  # Promotion level
            }

            # Add sold time if the car is sold
            if sold_time:
                data["sold_time"] = sold_time

            yield data

        # Navigate to the next pages, from 0 to 2999
        current_page = response.url.split('page=')[1].split(
            '&')[0]  # Extract the current page number
        # Increment page number by 1
        next_page_number = int(current_page) + 1

        # Check if the current page is less than 3000, navigate to the next one
        if next_page_number < 3:
            next_page_url = f"https://auto.ria.com/uk/search/?lang_id=4&page={next_page_number}&countpage=100&category_id=1&custom=1&abroad=2"
            yield scrapy.Request(next_page_url, callback=self.parse)

    def extract_fuel_and_capacity(self, item):
        """Extracts fuel type and engine capacity, returning them separately."""
        fuel_text = self.extract_text(item, "li.item-char:has(i.icon-fuel)")

        if fuel_text:
            parts = fuel_text.split(", ")
            fuel_type = parts[0]  # First word is fuel type
            engine_capacity = int(float(
                parts[1].split()[0]) * 1000) if len(parts) > 1 else None  # Convert to ml
            return fuel_type, engine_capacity
        else:
            # Handle electric vehicles (if no fuel type)
            fuel_type = "Electric"  # Set this type for electric vehicles
            engine_capacity = None  # No engine capacity needed for electric vehicles
            return fuel_type, engine_capacity

    def extract_text(self, item, selector):
        """Returns the text inside <li>, removing nested tags and extra spaces."""
        return item.css(selector).xpath("normalize-space()").get()

    def get_sale_status(self, item):
        """Checks if the car has been sold and returns status and sold time."""
        sold_date = item.css(
            "span[data-sold-date]::attr(data-sold-date)").get()

        if sold_date:
            return "Sold", sold_date  # Return "Sold" status and sale date
        else:
            return "For Sale", None  # Return "For Sale" status if not sold

    def check_accident(self, item):
        """Checks if the car has been in an accident."""
        accident_info = item.css("span.state._red::text").get()
        if accident_info and "Був в ДТП" in accident_info:
            return True  # Return True if the car was in an accident
        return False  # No accident information

    def extract_promotion_level(self, item):
        """Extracts promotion level from the <a class="item small-promote-level"> element."""
        promotion = item.css("a.item.small-promote-level::attr(title)").get()
        return promotion if promotion else None
