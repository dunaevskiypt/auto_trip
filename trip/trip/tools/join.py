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

# Создание словаря для ускоренного поиска по id из sprintdata
sprintdata_dict = {item['id']: item for item in sprintdata}

# Проверяем, существует ли файл output_file_path
if os.path.exists(output_file_path):
    # Читаем текущие данные
    with open(output_file_path, 'r', encoding='utf-8') as output_file:
        existing_data = json.load(output_file)
    # Преобразуем существующие данные в словарь для удобного обновления
    existing_data_dict = {item['id']: item for item in existing_data}
else:
    existing_data_dict = {}

# Объединение данных
for car in exdata:
    car_id = car.get('id')
    if not car_id:
        continue

    # Проверяем, есть ли запись с таким id в существующих данных
    if car_id in existing_data_dict:
        # Проверяем, изменился ли статус
        existing_status = existing_data_dict[car_id].get('status')
        new_status = sprintdata_dict.get(car_id, {}).get('status')
        if existing_status != new_status:
            # Обновляем запись только статусом и другими полями из sprintdata
            existing_data_dict[car_id].update(sprintdata_dict[car_id])
    elif car_id in sprintdata_dict:
        # Если записи с таким id нет, добавляем новую запись
        merged_car = car.copy()
        sprint_info = sprintdata_dict[car_id]
        merged_car.update(sprint_info)
        existing_data_dict[car_id] = merged_car

# Преобразуем словарь обратно в список
updated_data = list(existing_data_dict.values())

# Сохранение объединённых данных в data_car.json
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    json.dump(updated_data, output_file, ensure_ascii=False, indent=4)

print(f"Данные успешно обновлены и сохранены в {output_file_path}")
