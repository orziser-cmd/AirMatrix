import json
from AirMatrix.models import Passenger, Flight
from AirMatrix.factories import TicketFactory, BaggageFactory

class TicketRepository:
    def __init__(self, file_path="data/sample_data.jsonl", ticket_factory=None):#מכיל קובץ של כרטיסים
        self.file_path = file_path
        # שלב 2: ה-Factory מוזרק מבחוץ - ה-Repository רק קורא ובודק, ולא מחליט איזו מחלקה ליצור
        self.ticket_factory = ticket_factory if ticket_factory is not None else TicketFactory()

    def load_tickets_stream(self):  # טוענת את הקובץ וקוראת שורה שורה של כרטיס ומבצעת בדיקות ולידציה
        seen_ticket_ids = set()  # סט לשמירת מזהי כרטיסים שכבר נקלטו לצורך בדיקת כפילויות
        with open(self.file_path, "r", encoding="utf-8") as file:  # סטנדרט קריאה בינלאומי
            for line_number, line in enumerate(file, start=1):
                clean_line = line.strip()  # מוריד את הרווחים את הירידה שורה יוצר שורה נקייה
                if not clean_line:  # אם עדיין לא נקי תמשיך בתהליך
                    continue
                # אם סיימת לנקות תתחיל לבצע בדיקות ולידציה
                try:
                    data = json.loads(clean_line)
                    required_keys = ["ticket_id", "passenger_name", "flight_number", "base_price",
                                     "seat_number"]  # כל השדות הרשומים
                    for key in required_keys:
                        if key not in data:  # אם חסר שדה תקפיץ שגיאה
                            raise ValueError(f"שדה חסר: {key}")  # בדיקת שדה חסר

                    # בדיקת מזהי כרטיסים כפולים בזמן טעינת הנתונים (לבקשת המרצה)
                    ticket_id = data["ticket_id"]
                    if ticket_id in seen_ticket_ids:
                        raise ValueError(f"מזהה כרטיס כפול נמצא בקובץ: {ticket_id}")
                    seen_ticket_ids.add(ticket_id)

                    # ממשיך לרוץ עדיין בלולאה
                    if float(data["base_price"]) < 0:  # בדיקת ערכים לא תקינים במקרה הזה אם המחיר כרטיס שלילי
                        raise ValueError("מחיר כרטיס לא יכול להיות שלילי")

                    # יצירת אובייקט Passenger בהתאם ל-פרמטרים ב-models.py
                    passenger_id = f"PID_{ticket_id}"
                    passport_num = f"P{line_number:05d}"
                    passenger_obj = Passenger(
                        passenger_id=passenger_id,
                        full_name=data["passenger_name"],
                        passport_number=passport_num
                    )

                    # ה-Factory בוחר EconomyTicket / BusinessTicket וממיר דרך from_dict
                    ticket_obj = self.ticket_factory.create(data, passenger_obj)

                    yield ticket_obj  # תציג לי מה קיים באובייקט כרטיס לפי השדות שדרשנו

                except (ValueError, KeyError) as error:  # במידה והתקבלו אחת מהשגיאות הבאות תציג באיזה שורה השגיאה קיימת
                    print(f"שגיאה בשורה {line_number}: {error}")

    def find_ticket_by_id(self, ticket_id):#איתור כרטיס לפי מזהה - עובר על הקובץ בהדרגה ועוצר כשנמצא
        for ticket in self.load_tickets_stream():
            if ticket.ticket_id == ticket_id:
                return ticket
        return None  # לא נמצא כרטיס עם המזהה המבוקש

class BaggageRepository:#קריאת קובץ נתוני הכבודה הנוסף ובדיקת קשרים לכרטיסי טיסה קיימים
    def __init__(self, file_path="data/baggage_data.jsonl", baggage_factory=None):#מכיל קובץ של נתוני כבודה
        self.file_path = file_path
        self.baggage_factory = baggage_factory if baggage_factory is not None else BaggageFactory()

    def load_baggage_stream(self, valid_ticket_ids=None):#על אותו עקרון כמו קודם קורא את הקובץ
        with open(self.file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                clean_line = line.strip()#מנקה את השורות מוריד רווחים וירידת שורה
                if not clean_line:#אם השורה לא נקייה תמשיך לבצע
                    continue

                try:
                    data = json.loads(clean_line)#נכנס לפה אחרי שהשורה עברה ניקוי וטוען את השורות
                    required_keys = ["bag_id", "ticket_id", "weight_kg"]#שדות מזהים
                    for key in required_keys:
                        if key not in data:#בדיקת שדות חסרים
                            raise ValueError(f"שדה חסר ברשומת כבודה: {key}")

                    ticket_id = data["ticket_id"]#
                    # בדיקת קשרים: האם הכרטיס המקושר למזוודה אכן קיים במערכת
                    if valid_ticket_ids is not None and ticket_id not in valid_ticket_ids:
                        raise ValueError(f"מזוודה מקושרת לכרטיס שאינו קיים: {ticket_id}")

                    bag_item = self.baggage_factory.create(data)  # Factory: מזוודה רגילה או מטען רגיש

                    yield bag_item#תציג לי מה קיים באובייקט מזוודה לפי השדות שדרשנו

                except (ValueError, KeyError) as error:#במידה והתקבלו אחת מהשגיאות הבאות תציג באיזה שורה השגיאה קיימת
                    print(f"שגיאת כבודה בשורה {line_number}: {error}")


class FlightRepository:#שלב 2: קריאת קובץ הטיסות (כולל קואורדינטות היעד לשירות מזג האוויר)
    def __init__(self, file_path="data/flights.jsonl"):
        self.file_path = file_path

    def load_flights_stream(self):#אותו עיקרון: שורה אחר שורה, json.loads, בדיקות, from_dict
        seen_numbers = set()
        with open(self.file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    data = json.loads(clean_line)
                    for key in ["flight_number", "origin", "destination", "capacity", "latitude", "longitude"]:
                        if key not in data:
                            raise ValueError(f"שדה חסר ברשומת טיסה: {key}")
                    if data["flight_number"] in seen_numbers:
                        raise ValueError(f"מספר טיסה כפול: {data['flight_number']}")
                    seen_numbers.add(data["flight_number"])
                    yield Flight.from_dict(data)
                except (ValueError, KeyError) as error:
                    print(f"שגיאת טיסה בשורה {line_number}: {error}")
