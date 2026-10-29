# services.py - השכבה העסקית: מה עושים עם נתוני מזג האוויר.
# api_client.py רק מביא נתון תקין או זורק שגיאה; כאן מחליטים אם לעכב מטען רגיש ולפתוח פנייה.
# זהו התהליך המשולב: מערכת מרכזית (Flight) + שירות חיצוני (מזג אוויר) -> תת-מערכת הכבודה.
import logging

from AirMatrix.api_client import WeatherServiceError
from AirMatrix.models import GroundIncident

logger = logging.getLogger(__name__)


class FlightWeatherCheck:#תוצאת הבדיקה של טיסה אחת - מה הוחלט ולמה
    CLEAR = "CLEAR"                # אין מטען רגיש, או שכולו בטוח להטסה
    HOLD = "HOLD"                  # לפחות פריט אחד עוכב בגלל מזג האוויר
    MANUAL_CHECK = "MANUAL_CHECK"  # השירות לא זמין - לא מעדכנים כלום, צוות הקרקע בודק ידנית

    def __init__(self, flight_number, status, weather=None, held_items=None,
                 cleared_items=None, incidents=None, error=None, destination=None, destination_city=None):
        self.flight_number = flight_number
        self.destination = destination            # קוד שדה התעופה, למשל DXB
        self.destination_city = destination_city  # שם העיר, למשל Dubai
        self.status = status
        self.weather = weather
        self.held_items = held_items or []
        self.cleared_items = cleared_items or []
        self.incidents = incidents or []
        self.error = error

    def __str__(self):
        weather = str(self.weather) if self.weather else "no weather data"
        return (f"{self.flight_number} -> {self.destination}: {self.status} | {weather} | held={len(self.held_items)}, "
                f"cleared={len(self.cleared_items)}")


class CargoWeatherService:
    def __init__(self, weather_client):
        # weather_client מוזרק מבחוץ: WeatherApiClient (רשת) או SimulatedWeatherClient (ללא רשת),
        # ובבדיקות - Mock. לשירות לא משנה מאיפה הנתון מגיע, כל עוד יש fetch_current_weather.
        self.weather_client = weather_client
        self.incidents = []  # כל הפניות שנפתחו - ישמשו את הדוח המשולב
        self._next_incident_number = 1

    def check_flight(self, flight, items):
        # 1. מסננים רק פריטים רגישים שעדיין אפשר לעכב (פולימורפיזם - בלי לבדוק את סוג המחלקה)
        sensitive = [item for item in items
                     if item.is_temperature_sensitive() and item.status in ("CHECKED_IN", "SCREENED")]
        if not sensitive:
            # אין צורך לפנות לשירות - חוסך קריאת רשת מיותרת
            return FlightWeatherCheck(flight.flight_number, FlightWeatherCheck.CLEAR,
                                      destination=flight.destination, destination_city=flight.destination_city)

        # 2. מבקשים מזג אוויר ביעד. בכשל - לא נוגעים במצב הפריטים (מניעת עדכון עסקי שגוי)
        try:
            weather = self.weather_client.fetch_current_weather(flight.latitude, flight.longitude)
        except WeatherServiceError as error:
            logger.error("Weather check failed for %s: %s", flight.flight_number, error)
            return FlightWeatherCheck(flight.flight_number, FlightWeatherCheck.MANUAL_CHECK, error=str(error),
                                      destination=flight.destination, destination_city=flight.destination_city)

        # 3. ההחלטה העסקית: פריט שאינו בטוח לטמפרטורה ביעד - מעוכב, ונפתחת פנייה
        held, cleared, new_incidents = [], [], []
        for item in sensitive:
            if item.is_safe_for(weather.temperature_c):
                cleared.append(item)
                continue
            min_temp, max_temp = item.TEMPERATURE_LIMITS[item.cargo_category]
            reason = (f"{weather.temperature_c}°C at {flight.destination} - outside the safe range "
                      f"for {item.cargo_category} ({min_temp} to {max_temp}°C)")
            item.hold_for_weather(reason)
            held.append(item)
            new_incidents.append(self._open_incident(flight.flight_number, item.baggage_id, reason))
            logger.info("Held %s on %s: %s", item.baggage_id, flight.flight_number, reason)

        status = FlightWeatherCheck.HOLD if held else FlightWeatherCheck.CLEAR
        return FlightWeatherCheck(flight.flight_number, status, weather, held, cleared, new_incidents,
                                  destination=flight.destination, destination_city=flight.destination_city)

    def check_all_flights(self, flights_by_number, manifests):
        # בדיקה לכל טיסה שיש לה מניפסט; טיסה שאינה קיימת במערכת - שגיאת קשר בין הנתונים
        results = []
        for flight_number, manifest in sorted(manifests.items()):
            flight = flights_by_number.get(flight_number)
            if flight is None:
                raise ValueError(f"Manifest refers to unknown flight: {flight_number}")
            results.append(self.check_flight(flight, manifest.items))
        return results

    def get_open_incidents(self):
        return [incident for incident in self.incidents if incident.status == "OPEN"]

    def _open_incident(self, flight_number, baggage_id, reason):
        incident = GroundIncident(f"INC-{self._next_incident_number:03d}", flight_number, baggage_id, reason)
        self._next_incident_number += 1
        self.incidents.append(incident)
        return incident
