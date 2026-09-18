import json
from AirMatrix.models import BusinessTicket, EconomyTicket, Passenger, BaggageItem

class TicketRepository:
    def __init__(self, file_path="data/sample_data.jsonl"):#מכיל קובץ של כרטיסים
        self.file_path = file_path

    def load_tickets_stream(self):#טוענת את הקובץ וקוראת שורה שורה של כרטיס ומבצעת בדיקות ולידציה
        with open(self.file_path, "r", encoding="utf-8") as file:  # סטנדרט קריאה בינלאומי
            for line_number, line in enumerate(file, start=1):
                clean_line = line.strip()#מוריד את הרווחים את הירידה שורה יוצר שורה נקייה
                if not clean_line:#אם עדיין לא נקי תמשיך בתהליך
                    continue
#אם סיימת לנקות תתחיל לבצע בדיקות ולידציה
                try:
                    data = json.loads(clean_line)
                    required_keys = ["ticket_id", "passenger_name", "flight_number", "base_price", "seat_number"]#כל השדות הרשומים
                    for key in required_keys:
                        if key not in data:#אם חסר שדה תקפיץ שגיאה
                            raise ValueError(f"שדה חסר: {key}")  # בדיקת שדה חסר
#ממשיך לרוץ עדיין בלולאה
                    if float(data["base_price"]) < 0:  # בדיקת ערכים לא תקינים במקרה הזה אם המחיר כרטיס שלילי
                        raise ValueError("מחיר כרטיס לא יכול להיות שלילי")

                    # יצירת אובייקט Passenger בהתאם ל-פרמטרים ב-models.py
                    passenger_id = f"PID_{data['ticket_id']}"
                    passport_num = f"P{line_number:05d}"
                    passenger_obj = Passenger(
                        passenger_id=passenger_id,
                        full_name=data["passenger_name"],
                        passport_number=passport_num
                    )

                    if data.get("is_business", False):  # המרה לאובייקט כרטיס מתאים - ביזנס
                        ticket_obj = BusinessTicket(
                            ticket_id=data["ticket_id"],
                            passenger=passenger_obj,
                            flight_number=data["flight_number"],
                            base_price=float(data["base_price"]),
                            seat_number=data["seat_number"]
                        )
                    else: #אם לא נכנס לתנאי כלומר הכרטיס הוא מסוג תיירים
                        ticket_obj = EconomyTicket(
                            ticket_id=data["ticket_id"],
                            passenger=passenger_obj,
                            flight_number=data["flight_number"],
                            base_price=float(data["base_price"]),
                            seat_number=data["seat_number"]
                        )

                    yield ticket_obj #תציג לי מה קיים באובייקט כרטיס לפי השדות שדרשנו

                except (ValueError, KeyError) as error: #במידה והתקבלו אחת מהשגיאות הבאות תציג באיזה שורה השגיאה קיימת
                    print(f"שגיאה בשורה {line_number}: {error}")


class BaggageRepository:#קריאת קובץ נתוני הכבודה הנוסף ובדיקת קשרים לכרטיסי טיסה קיימים
    def __init__(self, file_path="data/baggage_data.jsonl"):#מכיל קובץ של נתוני כבודה
        self.file_path = file_path

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

                    bag_item = BaggageItem(
                        baggage_id=data["bag_id"],
                        ticket_id=ticket_id,
                        weight_kg=float(data["weight_kg"]),
                        status=data.get("status", "CHECKED_IN")
                    )

                    yield bag_item#תציג לי מה קיים באובייקט מזוודה לפי השדות שדרשנו

                except (ValueError, KeyError) as error:#במידה והתקבלו אחת מהשגיאות הבאות תציג באיזה שורה השגיאה קיימת
                    print(f"שגיאת כבודה בשורה {line_number}: {error}")