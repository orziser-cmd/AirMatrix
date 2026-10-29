# בדיקות לתהליך המשולב (סעיף 6.4): קבצים -> Repository + Factory -> מניפסט -> שירות מזג אוויר
from unittest.mock import Mock

import pytest

from AirMatrix.api_client import WeatherConnectionError
from AirMatrix.models import BaggageManifest
from AirMatrix.repository import TicketRepository, BaggageRepository, FlightRepository
from AirMatrix.services import CargoWeatherService, FlightWeatherCheck


@pytest.fixture
def loaded_system(write_jsonl):
    # מערכת קטנה מלאה מקבצים זמניים: טיסה אחת לדובאי, שני כרטיסים, כלוב חיה ומזוודה רגילה
    flights_path = write_jsonl("flights.jsonl", [
        {"flight_number": "LY005", "origin": "TLV", "destination": "DXB", "destination_city": "Dubai",
         "latitude": 25.25, "longitude": 55.36, "capacity": 250}])
    tickets_path = write_jsonl("tickets.jsonl", [
        {"ticket_id": "TK1", "passenger_name": "A", "flight_number": "LY005", "base_price": 500, "seat_number": "1A"},
        {"ticket_id": "TK2", "passenger_name": "B", "flight_number": "LY005", "base_price": 900,
         "seat_number": "2A", "is_business": True}])
    bags_path = write_jsonl("bags.jsonl", [
        {"bag_id": "PET-1", "ticket_id": "TK1", "weight_kg": 8, "bag_type": "pet"},
        {"bag_id": "BAG-1", "ticket_id": "TK2", "weight_kg": 20}])

    flights = {f.flight_number: f for f in FlightRepository(flights_path).load_flights_stream()}
    tickets = {t.ticket_id: t for t in TicketRepository(tickets_path).load_tickets_stream()}
    manifests = {}
    for bag in BaggageRepository(bags_path).load_baggage_stream(valid_ticket_ids=set(tickets)):
        flight_number = tickets[bag.ticket_id].flight_number
        manifests.setdefault(flight_number, BaggageManifest(flight_number)).add_item(bag)
    return flights, tickets, manifests


def test_full_flow_holds_cargo_and_opens_incident(loaded_system, make_weather_client):
    flights, _, manifests = loaded_system
    service = CargoWeatherService(make_weather_client(33.0))

    results = service.check_all_flights(flights, manifests)

    assert [r.status for r in results] == [FlightWeatherCheck.HOLD]
    statuses = {item.baggage_id: item.status for item in manifests["LY005"].items}
    assert statuses == {"PET-1": "HELD_WEATHER", "BAG-1": "CHECKED_IN"}  # רק המטען הרגיש עוכב
    assert [i.baggage_id for i in service.get_open_incidents()] == ["PET-1"]


def test_service_failure_leaves_cargo_untouched(loaded_system):
    flights, _, manifests = loaded_system
    failing_client = Mock()
    failing_client.fetch_current_weather.side_effect = WeatherConnectionError("down")
    service = CargoWeatherService(failing_client)

    results = service.check_all_flights(flights, manifests)

    assert results[0].status == FlightWeatherCheck.MANUAL_CHECK
    assert all(item.status == "CHECKED_IN" for item in manifests["LY005"].items)  # אין עדכון שגוי
    assert service.incidents == []


def test_manifest_for_unknown_flight_is_rejected(loaded_system, make_weather_client):
    flights, _, manifests = loaded_system
    manifests["LY999"] = BaggageManifest("LY999")  # קשר לא תקין: מניפסט לטיסה שלא קיימת
    with pytest.raises(ValueError, match="unknown flight"):
        CargoWeatherService(make_weather_client(20.0)).check_all_flights(flights, manifests)
