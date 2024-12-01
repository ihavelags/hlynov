from curs_funcs import *
from sys import exit


#проверка пользовательских данных из консоли
try:
    unformated_date = argv[1]
    unload_date = datetime.strptime(unformated_date, '%d.%m.%Y').date()
    numeric_codes = argv[2:]
    if not numeric_codes:
        raise NameError
    numeric_codes = ''.join(numeric_codes).split(',')
except Exception as error:
    if isinstance(error, IndexError):
        logging.warning('не введена дата')
    elif isinstance(error, ValueError):
        logging.warning(f'введен некорректный формат даты, требуется дата в формате DD.MM.YYYY, введено: {unformated_date}')
    elif isinstance(error, NameError):
        logging.warning('не введены коды валют')
    exit(0)

#проверка ответа от сервера
response = curs_on_date(unload_date)
if not response.status_code == 200:
    logging.error(f'получен некоррктный ответ {response.status_code}')
    connection.close()
    exit(0)

xml_date = get_xml_date(response.text)

#проверка существования данных по дате
if xml_date == None:
    logging.error(f'данные за дату {unload_date} отсутствуют на сервере')
    connection.close()
    exit(0)

if xml_date != unload_date:
    logging.warning(f'данные за дату {unload_date} отсутствуют на сервере, будут выгружены данные за {xml_date}')

exist_id = exist_date(xml_date)

#проверка ранее загруженных в БД данных
if exist_id:
    logging.info(f'данные за дату {str(xml_date)} были загружены в БД ранее')
else:
    xml_to_db(response.text)
    logging.info(f'данные за дату {str(xml_date)} добавлены в БД')
    exist_id = exist_date(xml_date)

#формирование вывода и вывод
output = output_table(exist_id[0][0], numeric_codes)

header = ('Номер распоряжения', 'Дата установки курсов', 'Валюта', 'Номинал', 'Курс')
if not output:
    logging.info(f'в БД не найдены данные коды валют')
else:
    output.insert(0, header)
    print()
for line in output:
    print(*['{:^40}'.format(text) for text in line], sep='|', end='|\n')
    print('-' * 205)
    
connection.close()