import json
import os

# Пути к файлам
exdata_file_path = "/home/peter/Desktop/Parsers/autoscraper/trip/trip/data/exdata.json"
sprintdata_file_path = "/home/peter/Desktop/Parsers/autoscraper/trip/trip/data/sprintdata.json"
output_file_path = "/home/peter/Desktop/Parsers/autoscraper/trip/trip/data/data_car.json"

# Чтение данных из exdata.json
with open(exdata_file_path, 'r', encoding='utf-8') as exdata_file:
    exdata = json.load(exdata_file)

# Чтение данных из sprintdata.json
with open(sprintdata_file_path, 'r', encoding='utf-8') as sprintdata_file:
    sprintdata = json.load(sprintdata_file)

# Создание словаря для ускоренного поиска по id
sprintdata_dict = {item['id']: item for item in sprintdata}

# Объединение данных
merged_data = []
for car in exdata:
    car_id = car.get('id')
    if car_id and car_id in sprintdata_dict:
        # Объединение данных по совпадению id
        merged_car = car.copy()  # Создаем копию данных из exdata
        # Получаем информацию из sprintdata
        sprint_info = sprintdata_dict[car_id]
        merged_car.update(sprint_info)  # Объединяем данные
        merged_data.append(merged_car)

# Сохранение объединённых данных в data_car.json
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    json.dump(merged_data, output_file, ensure_ascii=False, indent=4)

print(f"Данные успешно объединены и сохранены в {output_file_path}")
