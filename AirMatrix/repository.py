import json
from models import BusinessTicket, EconomyTicket, Passenger

class TicketRepository:
    def __init__(self, file_path="data/sample_data.jsonl"):
        self.file_path = file_path

    def load_tickets_stream(self):
        with open(self.file_path, "r", encoding="utf-8") as file:  # סטנדרט קריאה בינלאומי
            for line_number, line in enumerate(file, start=1):
                clean_line = line.strip()
                if not clean_line:
                    continue

                try:
                    data = json.loads(clean_line)
                    required_keys = ["ticket_id", "passenger_name", "flight_number", "base_price", "seat_number"]
                    for key in required_keys:
                        if key not in data:
                            raise ValueError(f"שדה חסר: {key}")  # בדיקת שדה חסר

                    if float(data["base_price"]) < 0:  # בדיקת ערכים לא תקינים
                        raise ValueError("מחיר כרטיס לא יכול להיות שלילי")

                    # יצירת אובייקט Passenger בהתאם ל-3 הפרמטרים ב-models.py
                    passenger_id = f"PID_{data['ticket_id']}"
                    passport_num = f"P{line_number:05d}"
                    passenger_obj = Passenger(
                        passenger_id=passenger_id,
                        full_name=data["passenger_name"],
                        passport_number=passport_num
                    )

                    if data.get("is_business", False):  # המרה לאובייקט כרטיס מתאים
                        ticket_obj = BusinessTicket(
                            ticket_id=data["ticket_id"],
                            passenger=passenger_obj,
                            flight_number=data["flight_number"],
                            base_price=float(data["base_price"]),
                            seat_number=data["seat_number"]
                        )
                    else:
                        ticket_obj = EconomyTicket(
                            ticket_id=data["ticket_id"],
                            passenger=passenger_obj,
                            flight_number=data["flight_number"],
                            base_price=float(data["base_price"]),
                            seat_number=data["seat_number"]
                        )

                    yield ticket_obj

                except (ValueError, KeyError) as error:
                    print(f"שגיאה בשורה {line_number}: {error}")