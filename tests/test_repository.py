# בדיקות לקריאת קבצים בהדרגה - עם קבצים זמניים (tmp_path) ולא עם קובצי הנתונים האמיתיים
from AirMatrix.repository import TicketRepository, BaggageRepository


def test_ticket_repository_skips_invalid_lines(write_jsonl, capsys):
    path = write_jsonl("tickets.jsonl", [
        {"ticket_id": "TK1", "passenger_name": "A", "flight_number": "LY001", "base_price": 400, "seat_number": "1A"},
        {"ticket_id": "TK2", "passenger_name": "B", "flight_number": "LY001", "base_price": -5, "seat_number": "1B"},
        {"ticket_id": "TK1", "passenger_name": "C", "flight_number": "LY001", "base_price": 300, "seat_number": "1C"},
        {"ticket_id": "TK3", "passenger_name": "D", "flight_number": "LY001", "seat_number": "1D"},
    ])
    tickets = list(TicketRepository(path).load_tickets_stream())

    assert [t.ticket_id for t in tickets] == ["TK1"]  # מחיר שלילי, מזהה כפול ושדה חסר - נדחו
    output = capsys.readouterr().out
    assert "שורה 2" in output and "שורה 3" in output and "שורה 4" in output


def test_baggage_repository_rejects_unknown_ticket(write_jsonl):
    path = write_jsonl("bags.jsonl", [
        {"bag_id": "B1", "ticket_id": "TK1", "weight_kg": 10},
        {"bag_id": "B2", "ticket_id": "TK404", "weight_kg": 12},
    ])
    bags = list(BaggageRepository(path).load_baggage_stream(valid_ticket_ids={"TK1"}))
    assert [b.baggage_id for b in bags] == ["B1"]
