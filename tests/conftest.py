import pytest
import sqlite3


@pytest.fixture(autouse=True)
def create_clean_table():
    connection = sqlite3.connect('CursOnDate.db')

    cursor = connection.cursor()

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

    cursor.execute('DELETE FROM CURRENCY_ORDER')

    cursor.execute('DELETE FROM CURRENCY_RATES')

    connection.commit()

    connection.close()