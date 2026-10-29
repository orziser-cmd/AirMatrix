# factories.py - תבנית Factory: מקום אחד שמחליט איזה אובייקט ליצור לפי נתוני הקלט.
# כאן (ורק כאן) מותר if/elif לבחירת המחלקה. הקוד העסקי מקבל אובייקט מוכן ועובד מולו דרך
# הטיפוס המשותף (Ticket / BaggageItem / לקוח מזג אוויר), בלי לבדוק את סוגו.
from AirMatrix.models import BusinessTicket, EconomyTicket, BaggageItem, SpecialCargoItem
from AirMatrix.strategies import StandardBaggageFee, SpecialCargoFee
from AirMatrix.api_client import WeatherApiClient, SimulatedWeatherClient


class TicketFactory:#מערכת מרכזית: מילון -> EconomyTicket או BusinessTicket
    def create(self, data, passenger):
        if data.get("is_business", False):
            return BusinessTicket.from_dict(data, passenger)
        return EconomyTicket.from_dict(data, passenger)


class BaggageFactory:#תת-מערכת הכבודה: מילון -> BaggageItem או SpecialCargoItem, כולל אסטרטגיית העמלה
    SPECIAL_TYPES = {"pet": "PET", "perishable": "PERISHABLE"}  # bag_type בקובץ -> קטגוריה במודל

    def __init__(self, standard_fee=None, special_fee=None):
        # האסטרטגיות מוזרקות מבחוץ, כך שאפשר להחליף מדיניות תמחור בלי לגעת ב-Factory
        self.standard_fee = standard_fee if standard_fee is not None else StandardBaggageFee()
        self.special_fee = special_fee if special_fee is not None else SpecialCargoFee()

    def create(self, data):
        bag_type = data.get("bag_type", "standard")
        common = {
            "baggage_id": data["bag_id"],
            "ticket_id": data["ticket_id"],
            "weight_kg": float(data["weight_kg"]),
            "status": data.get("status", "CHECKED_IN"),
        }
        if bag_type in self.SPECIAL_TYPES:
            return SpecialCargoItem(cargo_category=self.SPECIAL_TYPES[bag_type],
                                    fee_strategy=self.special_fee, **common)
        elif bag_type in ("standard", "overweight"):
            return BaggageItem(fee_strategy=self.standard_fee, **common)
        else:
            raise ValueError(f"Unknown bag type: {bag_type}")


def create_weather_client(config):#בחירת מקור נתוני מזג האוויר לפי ההגדרות: אמיתי (רשת) או מדומה
    if config.use_live_api:
        return WeatherApiClient(config.weather_base_url, timeout=config.http_timeout,
                                max_attempts=config.max_attempts,
                                retry_delay_seconds=config.retry_delay_seconds)
    return SimulatedWeatherClient.from_file("data/simulated_weather.jsonl")
