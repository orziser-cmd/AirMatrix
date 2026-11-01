# בדיקות לדוח המשולב (סעיף 6.3) - פותח בשיטת TDD.
# המדד החדש: "עמלות מטען בסיכון" - כמה הכנסה מעמלות מטען רגיש תלויה בפריטים שמעוכבים כרגע,
# ומספר הנוסעים שהעיכוב פוגע בהם. זה עוזר להחליט באיזו טיסה לטפל קודם.
# הערכים הצפויים חושבו ידנית לפי כללי העסק, ולא באמצעות הקוד שנבדק.
from AirMatrix.models import (Passenger, EconomyTicket, BusinessTicket, BaggageItem, SpecialCargoItem,
                              BaggageManifest, GroundIncident)
from AirMatrix import reports


def build_dubai_scenario(dubai_flight):
    p1 = Passenger("PID_1", "A", "P1")
    p2 = Passenger("PID_2", "B", "P2")
    tickets = {
        "TK1": EconomyTicket("TK1", p1, "LY005", 500.0, "10A"),   # מחיר סופי 500
        "TK2": BusinessTicket("TK2", p2, "LY005", 900.0, "02A"),  # מחיר סופי 900 + 35 טרקלין = 935
    }
    pet = SpecialCargoItem("PET-1", "TK1", 8.0, "PET")            # עמלה: 150 + 8*8 = 214
    pet.hold_for_weather("too hot")
    food = SpecialCargoItem("FOOD-1", "TK2", 10.0, "PERISHABLE")  # עמלה 230, אבל לא מעוכב
    manifest = BaggageManifest("LY005")
    for item in (pet, food, BaggageItem("BAG-1", "TK2", 25.0)):
        manifest.add_item(item)
    incidents = [GroundIncident("INC-001", "LY005", "PET-1", "too hot")]
    return {"LY005": dubai_flight}, tickets, {"LY005": manifest}, incidents


def test_combined_report_merges_flight_and_baggage_data(dubai_flight):
    report = reports.build_combined_report(*build_dubai_scenario(dubai_flight))
    row = report["flights"]["LY005"]

    assert row["destination"] == "DXB"
    assert row["passengers"] == 2
    assert row["ticket_revenue"] == 1435.0   # 500 + 935
    assert row["bags"] == 3
    assert row["held_cargo"] == 1
    assert row["open_incidents"] == 1


def test_revenue_at_risk_counts_only_held_cargo(dubai_flight):
    report = reports.build_combined_report(*build_dubai_scenario(dubai_flight))

    assert report["flights"]["LY005"]["cargo_fees_at_risk"] == 214.0  # רק החיה המעוכבת, לא המזון
    assert report["flights"]["LY005"]["affected_passengers"] == 1
    assert report["totals"]["cargo_fees_at_risk"] == 214.0


def test_closed_incidents_are_not_counted(dubai_flight):
    flights, tickets, manifests, incidents = build_dubai_scenario(dubai_flight)
    incidents[0].close()

    report = reports.build_combined_report(flights, tickets, manifests, incidents)

    assert report["flights"]["LY005"]["open_incidents"] == 0
    assert report["totals"]["open_incidents"] == 0
