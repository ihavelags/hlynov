from curs_funcs import *
import pytest
from datetime import date
from contextlib import nullcontext as does_not_raise


@pytest.mark.parametrize(
        'unload_date, expectation',
        [
            ('2024-11-11', 200),
            ('sdadsa', 500),
            ('0001-01-01', 200),
            ('1980-01-0', 500),
            (1, 500)
        ])
def test_curs_on_date(unload_date, expectation):
    assert curs_on_date(unload_date).status_code == expectation


@pytest.mark.parametrize(
        'unload_date, expectation, expected_error',
        [
            ('2024-11-23', date(2024, 11, 23), does_not_raise()),
            ('0001-01-01', None, does_not_raise()),
            ('1980-01-01', None, does_not_raise()),
            ('2025-01-01', None, does_not_raise()),
            (1, None, pytest.raises(ET.ParseError))
        ])
def test_get_xml_date(unload_date, expectation, expected_error):
    with expected_error:
        assert get_xml_date(curs_on_date(unload_date).text) == expectation


@pytest.mark.parametrize(
        'xml, expectation, expected_error',
        [
            (curs_on_date('2024-11-23'), [(739213, '2024-11-23')], does_not_raise()),
            (curs_on_date('2024-11-30'), [(739220, '2024-11-30')], does_not_raise()),
            (curs_on_date(1), None, pytest.raises(ET.ParseError))
        ])
def test_xml_to_db(xml, expectation, expected_error):
    with expected_error:
        xml_to_db(xml.text)
        cursor.execute('SELECT * FROM CURRENCY_ORDER')
        db_data = cursor.fetchall()
        assert db_data == expectation


@pytest.mark.parametrize(
        'unload_date, expectation',
        [
            ('2024-11-23', [(date(2024, 11, 23).toordinal(), )]),
            ('2024-11-30', [])
        ])
def test_exist_date(unload_date, expectation):
    xml = curs_on_date('2024-11-23')
    xml_to_db(xml.text)
    assert exist_date(unload_date) == expectation


@pytest.mark.parametrize(
        'id, numeric_codes, expectation',
        [
            (exist_date('2024-11-23'), [840, 51], [(739213, '2024-11-23', 'Армянский драм', 100, '26.3178'), (739213, '2024-11-23', 'Доллар США', 1, '102.5761')]),
            (exist_date('2024-11-23'), [], []),
            (exist_date('2024-11-23'), [36, 975], [(739213, '2024-11-23', 'Австралийский доллар', 1, '66.7155'), (739213, '2024-11-23', 'Болгарский лев', 1, '55.2051')])
        ])
def test_output_table(id, numeric_codes, expectation):
    xml = curs_on_date('2024-11-23')
    xml_to_db(xml.text)
    assert output_table(id[0][0], numeric_codes) == expectation