from AirMatrix.models import EconomyTicket, BusinessTicket, Passenger, BaggageManifest, Flight
from AirMatrix.repository import TicketRepository, BaggageRepository
from AirMatrix.context_managers import TemporaryDiscount
from AirMatrix.iterators import (FlightSchedule, active_business_tickets_generator, run_lazy_ticket_pipeline)
from AirMatrix.processing import (demonstrate_sorting, demonstrate_sets, build_tickets_by_id,
                                  group_tickets_by_passenger, process_security_queue,
                                  process_boarding_priority_queue, demonstrate_comprehensions)
from AirMatrix.reports import generate_baggage_manifest_report, format_weather_check, format_incident
from AirMatrix.repository import FlightRepository
from AirMatrix.config import AppConfig
from AirMatrix.factories import create_weather_client
from AirMatrix.services import CargoWeatherService
import logging
import sys


def main():
    print("=" * 60)
    print("1. טעינת נתונים והמרת DICT לאובייקטים (REPOSITORY)")
    print("=" * 60)

    # נתיב יחסי למיקום הקובץ שפועל בצורה יציבה מכל מקום
    repo = TicketRepository("data/sample_data.jsonl")

    loaded_tickets = []  # מאתחל רשימה ריקה של כרטיסים לאיסוף אובייקטים לבדיקות
    print("טעינת כרטיסים בהדרגה מהקובץ:")
    for ticket in repo.load_tickets_stream():
        print(f"  נטען: {ticket}")
        loaded_tickets.append(ticket)
    print(f"סך הכל נטענו {len(loaded_tickets)} כרטיסים תקינים.\n")

    print("=" * 60)
    print("2. הדגמת OOP ופולימורפיזם בקצרה")
    print("=" * 60)
    p_eco = Passenger("PID_E1", "Dana Cohen", "P11223")  # נוסע
    p_bus = Passenger("PID_B1", "Ron Levi", "P44556")  # נוסע
    demo_eco = EconomyTicket("T_ECO", p_eco, "LY001", 400.0, "15A")  # הגדרה של הנוסע בתור אקונומי הרכבה
    demo_bus = BusinessTicket("T_BUS", p_bus, "LY001", 1000.0, "02B")  # הגדרה של הנוסע בתור ביזנסס הרכבה

    print(f"כרטיס תיירים: {demo_eco.passenger.full_name}, מחיר סופי: {demo_eco.calculate_final_price()}")  # פולימורפיזם
    print(
        f"כרטיס עסקים: {demo_bus.passenger.full_name}, מחיר סופי: {demo_bus.calculate_final_price()}\n")  # פולימורפיזם מתווספת עלות כניסה לטרקלין

    print("=" * 60)
    print("3. מבני נתונים: set, dict, heapq ו-comprehensions (PROCESSING)")
    print("=" * 60)
    still_active, valid_cancel, cancel_check = demonstrate_sets(loaded_tickets, ["TK101", "TK999"])
    print(f"ביטולים שתואמים לכרטיס קיים (חיתוך): {sorted(valid_cancel)}")
    print(f"בדיקת השתייכות לכל ביטול (in): {dict(sorted(cancel_check.items()))}")
    print(f"כרטיסים שנשארו פעילים (הפרש): {len(still_active)}")

    tickets_by_id = build_tickets_by_id(loaded_tickets)  # מילון 1 - איתור לפי מזהה
    print(f"איתור לפי מזהה TK104: {tickets_by_id.get('TK104')}")
    _, count_per_passenger = group_tickets_by_passenger(loaded_tickets)  # מילון 2 - ספירה
    print(f"נוסעים עם כרטיסים: {len(count_per_passenger)}")

    boarding = process_boarding_priority_queue(loaded_tickets)  # heapq - עסקים לפני תיירים
    print(f"3 הראשונים בתור העלייה: {[t.ticket_id for t in boarding[:3]]}")

    prices, flight_numbers, seat_map = demonstrate_comprehensions(loaded_tickets)
    print(f"מספרי טיסות ייחודיים (set comprehension): {sorted(flight_numbers)}\n")

    print("=" * 60)
    print("3ב. מיון נתונים ופונקציות כערכים (PROCESSING)")
    print("=" * 60)
    by_price, by_seat, by_priority_and_price = demonstrate_sorting(loaded_tickets)  # מיון ב3 סוגי נתונים

    print("מיון לפי מחיר בסיס (מהנמוך לגבוה פונקציית key רגילה):")
    for t in by_price[:3]:
        print(f"  מזהה: {t.ticket_id}, מחיר בסיס: {t.base_price}")

    print("\nמיון לפי מושב (lambda קצרה):")
    for t in by_seat[:3]:
        print(f"  מזהה: {t.ticket_id}, מושב: {t.seat_number}")

    print("\nמיון לפי עדיפות עלייה ומחיר יורד (tuple של שני שדות):")
    for t in by_priority_and_price[:3]:
        print(f"  מזהה: {t.ticket_id}, עדיפות: {t.get_boarding_priority()}, מחיר סופי: {t.calculate_final_price()}")
    print()

    print("=" * 60)
    print("4. איטרטורים שני ITERATORS עצמאיים על אותו אובייקט")
    print("=" * 60)
    schedule = FlightSchedule()  # יצירת לוח טיסות ומכניס 3 אובייקטי Flight אמיתיים
    schedule.add_flight(Flight("LY001", "TLV", "FCO", 180))
    schedule.add_flight(Flight("LY002", "TLV", "CDG", 200))
    schedule.add_flight(Flight("LY003", "TLV", "LHR", 220))

    it1 = iter(schedule)
    it2 = iter(schedule)

    print(f"סורק א' פסיעה 1: {next(it1)}")
    print(f"סורק א' פסיעה 2: {next(it1)}")
    print(f"סורק ב' פסיעה 1 (עצמאי, מתחיל מההתחלה): {next(it2)}\n")

    print("=" * 60)
    print("5. הדגמת GENERATOR (התקדמות, עצירה, והתרוקנות)")
    print("=" * 60)
    gen = active_business_tickets_generator(loaded_tickets)
    print("הג'נרטור נוצר, עדיין לא התבצע שום עיבוד.")

    try:
        first_bus = next(gen)
        print(f"שליפה ידנית ראשונה (next): {first_bus}")

        print("המשך מעבר באמצעות לולאת for (ממשיך בדיוק מהנקודה שנעצר):")
        for remaining_bus in gen:
            print(f"  {remaining_bus}")

        print("ניסיון לעבור שוב על אותו ג'נרטור שהסתיים:")
        for t in gen:
            print(f"  {t}")
        print("הג'נרטור ריק (Exhausted) – לא הודפס דבר.\n")
    except StopIteration:
        print("לא נמצאו כרטיסי עסקים נוספים באוסף.\n")

    print("=" * 60)
    print("6. PIPELINE עצל (LAZY EVALUATION)")
    print("=" * 60)
    pipeline = run_lazy_ticket_pipeline(loaded_tickets)
    try:
        print(f"תוצאה ראשונה שנמשכה: {next(pipeline)}")
        print(f"תוצאה שנייה שנמשכה: {next(pipeline)}")
        print("הפעולה נעצרה – יתר הרשומות לא עובדו ולא נטענו לזיכרון.\n")
    except StopIteration:
        print("הפייפלין סיים את הנתונים הקיימים.\n")

    print("=" * 60)
    print("7. CONTEXT MANAGER (במצב רגיל ובמצב שגיאה)")
    print("=" * 60)
    test_passenger = Passenger("PID_TEST", "David Levi", "P99887")
    test_ticket = EconomyTicket("T101", test_passenger, "LY001", 500.0, "12C")
    print(f"מחיר התחלתי: {test_ticket.base_price}")

    # תרחיש תקין
    with TemporaryDiscount(test_ticket, 100.0) as t:
        print(f"בתוך בלוק ה-with (הנחה פעילה): {t.base_price}")
    print(f"המחיר חזר למקור -> {test_ticket.base_price}\n")

    # תרחיש שגיאה
    print("בדיקת שחזור מחיר בעת שגיאה:")
    try:
        with TemporaryDiscount(test_ticket, 150.0) as t:
            print(f"בתוך הבלוק לפני שגיאה: {t.base_price}")
            raise ValueError("תקלה מדומה בתהליך התשלום!")
    except ValueError as e:
        print(f"החריגה נתפסה בהצלחה: {e}")

    print(f" המחיר שוחזר בהצלחה -> {test_ticket.base_price}")
    print("=" * 60)

    # 8. ניהול כבודה ומניפסט (שילוב ההרחבה כנדרש)
    print("8. ניהול כבודה ומניפסט (BaggageManifest & BaggageItem)")
    print("=" * 60)

    # בדיקת קשרים: מזוודה נקלטת רק אם הכרטיס שלה קיים בקובץ הכרטיסים
    bag_repo = BaggageRepository("data/baggage_data.jsonl")
    valid_ids = set(tickets_by_id)
    loaded_bags = list(bag_repo.load_baggage_stream(valid_ticket_ids=valid_ids))
    print(f"נקלטו {len(loaded_bags)} מזוודות המקושרות לכרטיסים קיימים.\n")

    # שיוך כל מזוודה למניפסט של הטיסה שלה - לפי הכרטיס (ולא טיסה קבועה)
    manifests = {}
    for bag in loaded_bags:
        flight_num = tickets_by_id[bag.ticket_id].flight_number
        if flight_num not in manifests:
            # קיבולת קטנה בכוונה (100 ק"ג) כדי שהדוח יראה גם מצב CRITICAL
            manifests[flight_num] = BaggageManifest(flight_num, max_total_weight_kg=100.0)
        try:
            manifests[flight_num].add_item(bag)
        except ValueError as error:  # חריגת משקל - המזוודה לא נכנסת למניפסט, התוכנית ממשיכה
            print(f"  {bag.baggage_id} לא נוספה: {error}")

    # תור FIFO לבידוק ביטחוני
    screened, held = process_security_queue(loaded_bags)
    print(f"בידוק ביטחוני (FIFO): עברו {len(screened)}, מעוכבות {len(held)}: {[b.baggage_id for b in held]}\n")

    for f_num in sorted(manifests):
        generate_baggage_manifest_report(manifests[f_num])
    print()

    # 9. שלב 2: תהליך משולב - מזג אוויר ביעד -> החלטה על מטען רגיש בתת-מערכת הכבודה
    print("=" * 60)
    print("9. בדיקת מזג אוויר ביעד ועיכוב מטען רגיש (SERVICES)")
    print("=" * 60)
    config = AppConfig.from_env()
    if "--live" in sys.argv:  # דרך מפורשת להפעיל את השירות האמיתי
        config.use_live_api = True
    source = "אמיתי מהרשת (Open-Meteo)" if config.use_live_api else "מדומה (ללא רשת)"
    print(f"מקור נתוני מזג האוויר: {source}")

    flights_by_number = {f.flight_number: f for f in FlightRepository("data/flights.jsonl").load_flights_stream()}
    weather_service = CargoWeatherService(create_weather_client(config))  # התלות מוזרקת מבחוץ
    for result in weather_service.check_all_flights(flights_by_number, manifests):
        for line in format_weather_check(result):
            print(f"  {line}")
        print()

    print("פניות פתוחות לצוות הקרקע:")
    for incident in weather_service.get_open_incidents():
        print(f"  {format_incident(incident)}")
    print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    main()