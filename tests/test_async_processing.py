# בדיקות לאיסוף האסינכרוני: אותן תוצאות, לפי סדר הקלט, וכשל אחד לא עוצר את האחרים
import asyncio

from AirMatrix.api_client import WeatherConnectionError
from AirMatrix.async_processing import (AsyncWeatherSource, collect_weather_sequential,
                                        collect_weather_concurrent)

# הראשון ברשימה הוא האיטי ביותר - כך סדר הסיום שונה מסדר הקלט
READINGS = {"FCO": (19.0, 5.0, 0.15), "CDG": (11.0, 5.0, 0.01), "LHR": None, "DXB": (31.0, 5.0, 0.05)}
INPUT_ORDER = ["FCO", "CDG", "LHR", "DXB"]


def summarize(results):
    return [(dest, r.temperature_c if not isinstance(r, Exception) else type(r).__name__) for dest, r in results]


def test_concurrent_matches_sequential_in_input_order():
    sequential = asyncio.run(collect_weather_sequential(AsyncWeatherSource(READINGS), INPUT_ORDER))
    source = AsyncWeatherSource(READINGS)
    concurrent = asyncio.run(collect_weather_concurrent(source, INPUT_ORDER))

    assert summarize(concurrent) == summarize(sequential)
    assert [dest for dest, _ in concurrent] == INPUT_ORDER       # תוצאה לכל מזהה, לפי סדר הקלט
    assert source.completion_order == ["CDG", "DXB", "FCO"]      # אבל הסיום היה בסדר אחר


def test_one_failure_does_not_stop_other_tasks():
    results = dict(asyncio.run(collect_weather_concurrent(AsyncWeatherSource(READINGS), INPUT_ORDER)))
    assert isinstance(results["LHR"], WeatherConnectionError)
    assert results["DXB"].temperature_c == 31.0
