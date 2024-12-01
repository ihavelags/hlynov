import requests
import logging
import xml.etree.ElementTree as ET
import sqlite3
from sys import argv
from datetime import datetime


#запрос SOAP
def curs_on_date(unload_date):

    url = 'https://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx?WSDL'

    SOAPEnvelope = f'''
    <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
      <soap12:Body>
        <GetCursOnDateXML xmlns="http://web.cbr.ru/">
          <On_date>{str(unload_date)}</On_date>
        </GetCursOnDateXML>
      </soap12:Body>
    </soap12:Envelope>'''

    options = {
      'Content-Type': 'application/soap+xml; charset=utf-8'
    }

    response = requests.post(url, data=SOAPEnvelope, headers=options)

    return response


#получение даты выгрузки из xml файла
def get_xml_date(xml):

    root = ET.fromstring(xml)

    xml_date_string = root.find('.//ValuteData').get('OnDate')

    if xml_date_string == 'Error' or xml_date_string == None:
        return None

    xml_date = datetime.strptime(xml_date_string, '%Y%m%d').date()

    return xml_date


#прогрузка xml файла в БД
def xml_to_db(xml):

    root = ET.fromstring(xml)

    xml_date = get_xml_date(xml)
    
    id = xml_date.toordinal()

    cursor.execute('INSERT INTO CURRENCY_ORDER (id, ondate) VALUES (?, ?)', (id, str(xml_date)))

    for valute in root.iter('ValuteCursOnDate'):
        currency = dict()
        for attribute in valute:
            currency[attribute.tag] = attribute.text.strip()
        if len(currency) != 6:
            logging.warning(f'у валюты {currency['Vname']} отсутствуют обязательные аргументы')
            continue
        cursor.execute('''INSERT INTO CURRENCY_RATES 
        (order_id, name, numeric_code, alphabetic_code, scale, rate) 
        VALUES (?, ?, ?, ?, ?, ?)''', 
        (id, currency['Vname'], currency['Vcode'], currency['VchCode'], int(currency['Vnom']), currency['Vcurs']))

    connection.commit()


#проверка существования данных по дате
def exist_date(unload_date):
    cursor.execute('SELECT id FROM CURRENCY_ORDER WHERE ondate = ?', (str(unload_date), ))
    return cursor.fetchall()


#формирование выходной таблицы
def output_table(id, numeric_codes):
    cursor.execute(f'''
    SELECT order_id, 
    (SELECT ondate FROM CURRENCY_ORDER WHERE id = order_id),
    name, scale, rate FROM CURRENCY_RATES 
    WHERE order_id = ? AND 
    numeric_code IN ({",".join(["?"] * len(numeric_codes))})''', (id, *numeric_codes))
    return cursor.fetchall()


filename = argv[0]


#логирование в файл и консоль
file_logger = logging.FileHandler(f'{filename[:-3]}.log')
console_logger = logging.StreamHandler()

logging.basicConfig(handlers=(file_logger, console_logger), 
                    format='%(asctime)s | %(levelname)s: %(message)s', 
                    datefmt='%d.%m.%Y %H:%M:%S',
                    level=logging.INFO)


#создание/подключение к БД
connection = sqlite3.connect('CursOnDate.db')


cursor = connection.cursor()


#создание таблиц если не существуют
cursor.execute('''
CREATE TABLE IF NOT EXISTS CURRENCY_ORDER (
id INT PRIMARY KEY,
ondate TEXT UNIQUE NOT NULL
)
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS CURRENCY_RATES (
order_id INT NOT NULL REFERENCES CURRENCY_ORDER (id),
name TEXT NOT NULL,
numeric_code TEXT NOT NULL,
alphabetic_code TEXT NOT NULL,
scale INT NOT NULL,
rate TEXT NOT NULL
)
''')


connection.commit()