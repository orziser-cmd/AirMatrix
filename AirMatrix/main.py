from models import EconomyTicket, BusinessTicket, Passenger
from repository import TicketRepository
from context_managers import TemporaryDiscount
from iterators import (FlightSchedule,active_business_tickets_generator,run_lazy_ticket_pipeline)
from processing import demonstrate_sorting


def main():
    print("=" * 60)
    print("1. טעינת נתונים והמרת DICT לאובייקטים (REPOSITORY)")
    print("=" * 60)

    # נתיב יחסי למיקום הקובץ שפועל בצורה יציבה מכל מקום
    repo = TicketRepository("../data/sample_data.jsonl")


    loaded_tickets = [] #מאתחל רשימה ריקה של כרטיסים לאיסוף אובייקטים לבדיקות
    print("טעינת כרטיסים בהדרגה מהקובץ:")
    for ticket in repo.load_tickets_stream():
        print(f"  נטען: {ticket}")
        loaded_tickets.append(ticket)
    print(f"סך הכל נטענו {len(loaded_tickets)} כרטיסים תקינים.\n")

    print("=" * 60)
    print("2. הדגמת OOP ופולימורפיזם בקצרה")
    print("=" * 60)
    p_eco = Passenger("PID_E1", "Dana Cohen", "P11223")#נוסע
    p_bus = Passenger("PID_B1", "Ron Levi", "P44556")#נוסע
    demo_eco = EconomyTicket("T_ECO", p_eco, "LY001", 400.0, "15A")#הגדרה של הנוסע בתור אקונומי- הרכבה
    demo_bus = BusinessTicket("T_BUS", p_bus, "LY001", 1000.0, "02B")#הגדרה של הנוסע בתור ביזנסס - הרכבה

    print(f"כרטיס תיירים: {demo_eco.passenger.full_name}, מחיר סופי: {demo_eco.calculate_final_price()}")#פולימורפיזם
    print(f"כרטיס עסקים: {demo_bus.passenger.full_name}, מחיר סופי: {demo_bus.calculate_final_price()}\n")#פולימורפיזם - מתווספת עלות כניסה לטרקלין

    print("=" * 60)
    print("3. מיון נתונים ופונקציות כערכים (PROCESSING)")
    print("=" * 60)
    by_price, by_seat, by_priority_and_price = demonstrate_sorting(loaded_tickets)#מיון ב3 סוגי נתונים

    print("מיון לפי מחיר בסיס (מהנמוך לגבוה - פונקציית key רגילה):")
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
    print("4. איטרטורים - שני ITERATORS עצמאיים על אותו אובייקט")
    print("=" * 60)
    schedule = FlightSchedule() #יצירת לוח טיסות ומכניס 3 טיסות
    schedule.add_flight("טיסה 101 לרומא")
    schedule.add_flight("טיסה 202 לפריז")
    schedule.add_flight("טיסה 303 ללונדון")

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


if __name__ == "__main__":
    main()