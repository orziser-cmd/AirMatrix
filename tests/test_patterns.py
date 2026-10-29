# בדיקות לתבניות התכנון: Strategy (עמלות) ו-Factory (יצירת כרטיסים ומזוודות)
import pytest

from AirMatrix.factories import TicketFactory, BaggageFactory
from AirMatrix.models import EconomyTicket, BusinessTicket, BaggageItem, SpecialCargoItem
from AirMatrix.strategies import StandardBaggageFee, SpecialCargoFee


# אותו משקל, שתי אסטרטגיות -> שתי תוצאות שונות (חושב ידנית)
@pytest.mark.parametrize("strategy, weight, expected", [
    (StandardBaggageFee(), 20.0, 0.0),      # מתחת ל-23 ק"ג - חינם
    (StandardBaggageFee(), 25.0, 24.0),     # 2 ק"ג חריגים * 12
    (SpecialCargoFee(), 10.0, 230.0),       # 150 + 10 * 8
])
def test_fee_strategies(strategy, weight, expected):
    assert strategy.calculate_fee(weight) == expected


def test_bag_delegates_fee_to_injected_strategy():
    # אותה מזוודה עם אסטרטגיה אחרת שהוזרקה מבחוץ - העמלה משתנה בלי לשנות את המחלקה
    bag = BaggageItem("BAG-1", "TK1", 25.0, fee_strategy=StandardBaggageFee(price_per_extra_kg=20.0))
    assert bag.calculate_fee() == 40.0


@pytest.mark.parametrize("is_business, expected_class", [(True, BusinessTicket), (False, EconomyTicket)])
def test_ticket_factory_chooses_class(passenger, is_business, expected_class):
    data = {"ticket_id": "TK1", "flight_number": "LY001", "base_price": 500, "seat_number": "1A",
            "is_business": is_business}
    assert type(TicketFactory().create(data, passenger)) is expected_class


def test_baggage_factory_creates_special_cargo_with_special_fee():
    item = BaggageFactory().create({"bag_id": "B1", "ticket_id": "TK1", "weight_kg": 8, "bag_type": "pet"})
    assert isinstance(item, SpecialCargoItem)
    assert item.cargo_category == "PET"
    assert isinstance(item.fee_strategy, SpecialCargoFee)


def test_baggage_factory_creates_standard_bag():
    item = BaggageFactory().create({"bag_id": "B2", "ticket_id": "TK1", "weight_kg": 20})
    assert type(item) is BaggageItem
    assert item.is_temperature_sensitive() is False


def test_baggage_factory_rejects_unknown_type():
    with pytest.raises(ValueError, match="Unknown bag type"):
        BaggageFactory().create({"bag_id": "B3", "ticket_id": "TK1", "weight_kg": 5, "bag_type": "piano"})
