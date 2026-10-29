# async_processing.py - איסוף אסינכרוני של מזג אוויר עבור כמה יעדים (סעיף 5.1)
# המשימות עצמאיות: הבדיקה של דובאי לא צריכה את התוצאה של אוסלו כדי להתחיל.
# זו סימולציה: ההמתנה לרשת מדומה ב-await asyncio.sleep, והנתונים מקומיים (data/simulated_weather.jsonl).
# אין כאן time.sleep ואין קריאות HTTP חוסמות - הן היו עוצרות את כל לולאת האירועים.
import asyncio
import json
import logging

from AirMatrix.api_client import WeatherConnectionError, WeatherDataError
from AirMatrix.models import WeatherReport

logger = logging.getLogger(__name__)


class AsyncWeatherSource:#מקור מזג אוויר מדומה שעונה אחרי זמן המתנה שונה לכל יעד
    def __init__(self, readings):
        # readings: {קוד יעד: (טמפרטורה, רוח, זמן המתנה בשניות)}; ערך None = תקלה מדומה
        self.readings = readings
        self.completion_order = []  # סדר הסיום בפועל - כדי להראות שהוא שונה מסדר הקלט

    @classmethod
    def from_file(cls, path):#קריאה שורה אחר שורה מאותו קובץ נתונים מדומים
        readings = {}
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if data.get("simulate_failure", False):
                    readings[data["destination"]] = None
                else:
                    readings[data["destination"]] = (float(data["temperature_c"]),
                                                     float(data["wind_speed_kmh"]),
                                                     float(data.get("delay_seconds", 0.2)))
        return cls(readings)

    async def fetch(self, destination):
        if destination not in self.readings:
            raise WeatherDataError(f"No simulated weather for {destination}")
        reading = self.readings[destination]
        if reading is None:
            await asyncio.sleep(0.05)
            raise WeatherConnectionError(f"Simulated outage for {destination}")
        temperature, wind, delay = reading
        await asyncio.sleep(delay)  # "המתנה לרשת" שלא חוסמת: בזמן הזה משימות אחרות רצות
        self.completion_order.append(destination)
        return WeatherReport(None, None, temperature, wind, observed_at="simulated", is_simulated=True)


async def _fetch_one(source, destination):
    # עוטפת משימה אחת: בכשל מחזירה את השגיאה כתוצאה, כדי שכשל ביעד אחד לא יעצור את האחרים
    try:
        return destination, await source.fetch(destination)
    except (WeatherConnectionError, WeatherDataError) as error:
        logger.warning("Async weather fetch failed for %s: %s", destination, error)
        return destination, error


async def collect_weather_sequential(source, destinations):
    # גרסה סדרתית: ממתינים לסיום כל משימה לפני שמתחילים את הבאה. זמן כולל = סכום ההמתנות
    results = []
    for destination in destinations:
        results.append(await _fetch_one(source, destination))
    return results


async def collect_weather_concurrent(source, destinations):
    # גרסה אסינכרונית: קודם מתזמנים את כל המשימות (create_task), ורק אחר כך אוספים (gather).
    # זמן כולל = בערך ההמתנה הארוכה ביותר. gather מחזיר את התוצאות לפי סדר הקלט,
    # גם אם משימה מאוחרת ברשימה הסתיימה ראשונה.
    tasks = [asyncio.create_task(_fetch_one(source, destination)) for destination in destinations]
    return list(await asyncio.gather(*tasks))
