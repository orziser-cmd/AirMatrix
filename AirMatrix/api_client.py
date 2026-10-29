# api_client.py - תקשורת בלבד מול שירות מזג האוויר Open-Meteo (https://open-meteo.com/en/docs)
# האחריות כאן: לשלוח GET, לזהות כשלים, לנסות שוב כשצריך, ולבדוק שהתשובה תקינה.
# מה עושים עם הטמפרטורה (לעכב מטען או לא) - זו החלטה עסקית, והיא נמצאת ב-services.py.
import logging
import time

import requests

from AirMatrix.models import WeatherReport

logger = logging.getLogger(__name__)


# ---------- סוגי שגיאות: כל כשל מקבל שם משלו, כדי שהשכבה העסקית תדע מה קרה ----------
class WeatherServiceError(Exception):
    """מחלקת בסיס לכל שגיאות שירות מזג האוויר."""


class WeatherConnectionError(WeatherServiceError):
    """כשל תקשורת (Timeout / ConnectionError) שנמשך גם אחרי כל הניסיונות."""


class WeatherHTTPError(WeatherServiceError):
    """השרת החזיר קוד שגיאה (4xx / 5xx). לא מנסים שוב."""


class WeatherDataError(WeatherServiceError):
    """התשובה אינה JSON תקין, או שחסרים בה שדות / ערכים לא הגיוניים. לא מנסים שוב."""


class WeatherApiClient:
    def __init__(self, base_url, timeout=5.0, max_attempts=3, retry_delay_seconds=1.0,
                 session=None, sleep_func=time.sleep):
        # התלויות מוזרקות מבחוץ: בבדיקות מעבירים session מדומה ו-sleep_func שלא באמת ממתין
        self.base_url = base_url
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.session = session if session is not None else requests.Session()
        self.sleep_func = sleep_func

    def fetch_current_weather(self, latitude, longitude):
        # פעולה ציבורית: מחזירה WeatherReport או זורקת אחת משגיאות WeatherServiceError
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m",  # רק השדות שהמערכת צריכה
        }
        response = self._get_with_retry(params)
        payload = self._decode_json(response)
        return self._parse_weather(payload, latitude, longitude)

    def _get_with_retry(self, params):
        # Retry רק על Timeout / ConnectionError - בעיות זמניות שסביר שיעברו
        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.info("GET %s (attempt %d/%d)", self.base_url, attempt, self.max_attempts)
                response = self.session.get(self.base_url, params=params, timeout=self.timeout)
                response.raise_for_status()  # 4xx/5xx -> HTTPError
                return response
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as error:
                logger.warning("Weather request failed (attempt %d/%d): %s",
                               attempt, self.max_attempts, type(error).__name__)
                if attempt == self.max_attempts:
                    logger.error("Weather service unreachable after %d attempts", self.max_attempts)
                    raise WeatherConnectionError(
                        f"Weather service unreachable after {self.max_attempts} attempts") from error
                self.sleep_func(self.retry_delay_seconds * attempt)  # המתנה הולכת וגדלה: 1, 2 שניות
            except requests.exceptions.HTTPError as error:
                # שגיאת HTTP (למשל 400 פרמטרים שגויים, 401/403 הרשאה) - ניסיון חוזר לא יעזור
                status = error.response.status_code if error.response is not None else "?"
                logger.error("Weather service returned HTTP %s", status)
                raise WeatherHTTPError(f"Weather service returned HTTP {status}") from error

    def _decode_json(self, response):
        try:
            return response.json()
        except ValueError as error:  # requests.JSONDecodeError יורשת מ-ValueError
            logger.error("Weather response is not valid JSON")
            raise WeatherDataError("Weather response is not valid JSON") from error

    def _parse_weather(self, payload, latitude, longitude):
        # בדיקת מבנה התשובה לפני שמאמינים לה
        current = payload.get("current") if isinstance(payload, dict) else None
        if not isinstance(current, dict):
            raise WeatherDataError("Missing 'current' section in weather response")

        for field in ("time", "temperature_2m", "wind_speed_10m"):
            if field not in current:
                raise WeatherDataError(f"Missing field '{field}' in weather response")

        temperature = current["temperature_2m"]
        wind_speed = current["wind_speed_10m"]
        if not _is_number(temperature) or not -90 <= temperature <= 60:
            raise WeatherDataError(f"Invalid temperature value: {temperature!r}")
        if not _is_number(wind_speed) or wind_speed < 0:
            raise WeatherDataError(f"Invalid wind speed value: {wind_speed!r}")

        return WeatherReport(latitude, longitude, float(temperature), float(wind_speed),
                             observed_at=current["time"], is_simulated=False)


def _is_number(value):
    # bool הוא תת-סוג של int בפייתון, ולכן מוציאים אותו במפורש
    return isinstance(value, (int, float)) and not isinstance(value, bool)


if __name__ == "__main__":
    # בדיקה ידנית מול השירות האמיתי (דורש רשת): python -m AirMatrix.api_client
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    client = WeatherApiClient("https://api.open-meteo.com/v1/forecast")
    print("Dubai (DXB):", client.fetch_current_weather(25.25, 55.36))
