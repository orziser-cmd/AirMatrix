# בדיקות ללקוח השירות החיצוני - בלי רשת ובלי המתנות אמיתיות.
# מחליפים את התלות החיצונית (session של requests, sleep) ולא את הפונקציה שנבדקת.
from unittest.mock import Mock, patch

import pytest
import requests

from AirMatrix.api_client import (WeatherApiClient, WeatherConnectionError, WeatherHTTPError,
                                  WeatherDataError)

VALID_PAYLOAD = {"current": {"time": "2026-10-29T15:30", "temperature_2m": 29.9, "wind_speed_10m": 6.4}}


def make_response(status_code=200, payload=None, invalid_json=False):
    response = Mock()
    response.status_code = status_code
    if status_code >= 400:
        error = requests.exceptions.HTTPError(f"{status_code} error")
        error.response = response
        response.raise_for_status.side_effect = error
    if invalid_json:
        response.json.side_effect = requests.exceptions.JSONDecodeError("bad", "doc", 0)
    else:
        response.json.return_value = payload
    return response


@pytest.fixture
def sleep_spy():
    return Mock()  # מחליף את time.sleep - הבדיקה לא ממתינה באמת


def make_client(session, sleep_spy):
    return WeatherApiClient("https://example.test/forecast", timeout=2, max_attempts=3,
                            retry_delay_seconds=1, session=session, sleep_func=sleep_spy)


def test_success_returns_weather_report(sleep_spy):
    session = Mock()
    session.get.return_value = make_response(payload=VALID_PAYLOAD)

    report = make_client(session, sleep_spy).fetch_current_weather(25.25, 55.36)

    assert report.temperature_c == 29.9
    assert report.wind_speed_kmh == 6.4
    assert report.is_simulated is False
    # נשלחו הפרמטרים וה-timeout הנכונים
    _, kwargs = session.get.call_args
    assert kwargs["timeout"] == 2
    assert kwargs["params"]["latitude"] == 25.25


def test_retry_succeeds_after_temporary_timeout(sleep_spy):
    session = Mock()
    session.get.side_effect = [requests.exceptions.Timeout(), make_response(payload=VALID_PAYLOAD)]

    report = make_client(session, sleep_spy).fetch_current_weather(1, 1)

    assert report.temperature_c == 29.9
    assert session.get.call_count == 2
    sleep_spy.assert_called_once_with(1)  # המתנה אחת בין הניסיונות


def test_retry_stops_after_three_attempts(sleep_spy):
    session = Mock()
    session.get.side_effect = requests.exceptions.ConnectionError()

    with pytest.raises(WeatherConnectionError, match="3 attempts"):
        make_client(session, sleep_spy).fetch_current_weather(1, 1)
    assert session.get.call_count == 3
    assert sleep_spy.call_count == 2  # המתנה רק בין ניסיונות, לא אחרי האחרון


def test_http_error_is_not_retried(sleep_spy):
    session = Mock()
    session.get.return_value = make_response(status_code=503)

    with pytest.raises(WeatherHTTPError, match="503"):
        make_client(session, sleep_spy).fetch_current_weather(1, 1)
    assert session.get.call_count == 1
    sleep_spy.assert_not_called()


@pytest.mark.parametrize("payload", [
    {"current": {"time": "t", "wind_speed_10m": 5}},                          # חסר temperature_2m
    {"current": {"time": "t", "temperature_2m": "hot", "wind_speed_10m": 5}},  # טמפרטורה לא מספרית
    {"hourly": {}},                                                           # אין current בכלל
])
def test_invalid_data_raises_data_error_without_retry(sleep_spy, payload):
    session = Mock()
    session.get.return_value = make_response(payload=payload)

    with pytest.raises(WeatherDataError):
        make_client(session, sleep_spy).fetch_current_weather(1, 1)
    assert session.get.call_count == 1


def test_malformed_json_raises_data_error(sleep_spy):
    session = Mock()
    session.get.return_value = make_response(invalid_json=True)
    with pytest.raises(WeatherDataError, match="not valid JSON"):
        make_client(session, sleep_spy).fetch_current_weather(1, 1)


def test_default_session_is_requests_session():
    # patch מחליף את requests.Session כדי לוודא שהלקוח משתמש בו כשלא הוזרק session
    with patch("AirMatrix.api_client.requests.Session") as session_class:
        session_class.return_value.get.return_value = make_response(payload=VALID_PAYLOAD)
        client = WeatherApiClient("https://example.test/forecast")
        client.fetch_current_weather(1, 1)
    session_class.assert_called_once()
