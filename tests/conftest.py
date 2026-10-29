# conftest.py - Fixtures משותפים לכל קובצי הבדיקות.
# pytest מזהה את הקובץ אוטומטית; כל פונקציה עם @pytest.fixture זמינה כפרמטר בכל בדיקה.
import json
from unittest.mock import Mock

import pytest

from AirMatrix.models import Passenger, EconomyTicket, BusinessTicket, Flight, WeatherReport


@pytest.fixture
def passenger():
    return Passenger("PID_1", "Test Passenger", "P00001")


@pytest.fixture
def economy_ticket(passenger):
    return EconomyTicket("TK1", passenger, "LY001", 400.0, "15A")


@pytest.fixture
def business_ticket(passenger):
    return BusinessTicket("TK2", passenger, "LY001", 1000.0, "02B")


@pytest.fixture
def dubai_flight():
    return Flight("LY005", "TLV", "DXB", 250, destination_city="Dubai", latitude=25.25, longitude=55.36)


@pytest.fixture
def write_jsonl(tmp_path):
    # מחזיר פונקציה שכותבת רשומות לקובץ JSONL זמני (tmp_path נמחק בסוף הבדיקה)
    def _write(name, records):
        path = tmp_path / name
        path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        return str(path)
    return _write


@pytest.fixture
def make_weather_client():
    # Mock שמחליף את שירות מזג האוויר: מחזיר תמיד דיווח עם הטמפרטורה שנבחרה
    def _make(temperature_c):
        client = Mock()
        client.fetch_current_weather.return_value = WeatherReport(0, 0, temperature_c, 10.0, "test",
                                                                  is_simulated=True)
        return client
    return _make
