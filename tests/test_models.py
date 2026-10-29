# בדיקות למודל משלב 1 (לוודא שההתנהגות נשמרה) ולמחלקות החדשות של שלב 2
import pytest

from AirMatrix.models import Ticket, Flight, BaggageItem, SpecialCargoItem


@pytest.mark.parametrize("capacity", [0, -5])
def test_flight_rejects_non_positive_capacity(capacity):
    with pytest.raises(ValueError, match="Capacity"):
        Flight("LY001", "TLV", "FCO", capacity)


def test_ticket_is_abstract(passenger):
    with pytest.raises(TypeError):
        Ticket("TK0", passenger, "LY001", 100.0, "1A")


# הערכים הצפויים חושבו ידנית לפי כללי המחיר:
# תיירים: 400 + 45 לכל מזוודה. עסקים: 1000 + 35 טרקלין, מזוודה ראשונה חינם ו-25 לכל נוספת.
@pytest.mark.parametrize("ticket_fixture, extra_bags, expected", [
    ("economy_ticket", 0, 400.0),
    ("economy_ticket", 3, 535.0),
    ("business_ticket", 1, 1035.0),
    ("business_ticket", 3, 1085.0),
])
def test_final_price_is_polymorphic(request, ticket_fixture, extra_bags, expected):
    ticket = request.getfixturevalue(ticket_fixture)
    assert ticket.calculate_final_price(extra_bags) == expected


def test_flight_rejects_duplicate_seat(economy_ticket, passenger):
    flight = Flight("LY001", "TLV", "FCO", 10)
    flight.add_ticket(economy_ticket)
    other = type(economy_ticket)("TK9", passenger, "LY001", 300.0, economy_ticket.seat_number)
    with pytest.raises(ValueError, match="already taken"):
        flight.add_ticket(other)
    assert len(flight) == 1  # הכרטיס הכפול לא נוסף


def test_negative_price_blocked_even_after_creation(economy_ticket):
    with pytest.raises(ValueError):
        economy_ticket.base_price = -1


# גבולות הטווח הבטוח לבעלי חיים: 7.0 עד 29.5 כולל
@pytest.mark.parametrize("temperature, expected", [
    (6.9, False),
    (7.0, True),
    (29.5, True),
    (29.6, False),
])
def test_pet_safe_temperature_boundaries(temperature, expected):
    pet = SpecialCargoItem("BAG-1", "TK1", 8.0, "PET")
    assert pet.is_safe_for(temperature) is expected


def test_loaded_cargo_cannot_be_held():
    pet = SpecialCargoItem("BAG-1", "TK1", 8.0, "PET", status="LOADED")
    with pytest.raises(ValueError, match="already loaded"):
        pet.hold_for_weather("too hot")
    assert pet.status == "LOADED"


def test_regular_bag_rejects_weather_hold_status():
    # HELD_WEATHER קיים רק במטען רגיש - מזוודה רגילה לא יכולה להיווצר במצב הזה
    with pytest.raises(ValueError, match="Unknown baggage status"):
        BaggageItem("BAG-2", "TK1", 10.0, status="HELD_WEATHER")
