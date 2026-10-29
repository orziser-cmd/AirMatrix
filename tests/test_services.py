# בדיקות להחלטה העסקית ב-CargoWeatherService (השירות מוחלף ב-Mock)
from AirMatrix.models import BaggageItem, SpecialCargoItem
from AirMatrix.services import CargoWeatherService, FlightWeatherCheck


def test_hot_destination_holds_pet_and_opens_incident(dubai_flight, make_weather_client):
    pet = SpecialCargoItem("BAG-1", "TK1", 8.0, "PET")
    service = CargoWeatherService(make_weather_client(31.0))

    result = service.check_flight(dubai_flight, [pet])

    assert result.status == FlightWeatherCheck.HOLD
    assert pet.status == "HELD_WEATHER"
    assert len(service.get_open_incidents()) == 1
    assert service.incidents[0].baggage_id == "BAG-1"


def test_safe_temperature_clears_cargo(dubai_flight, make_weather_client):
    pet = SpecialCargoItem("BAG-1", "TK1", 8.0, "PET")
    service = CargoWeatherService(make_weather_client(20.0))

    result = service.check_flight(dubai_flight, [pet])

    assert result.status == FlightWeatherCheck.CLEAR
    assert result.cleared_items == [pet]
    assert pet.status == "CHECKED_IN"
    assert service.incidents == []


def test_flight_without_sensitive_cargo_does_not_call_service(dubai_flight, make_weather_client):
    client = make_weather_client(45.0)
    service = CargoWeatherService(client)

    result = service.check_flight(dubai_flight, [BaggageItem("BAG-2", "TK1", 20.0)])

    assert result.status == FlightWeatherCheck.CLEAR
    client.fetch_current_weather.assert_not_called()  # לא בוזבזה קריאה לשירות
