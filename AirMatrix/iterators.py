#חלק ד'
# מחלקות Iterable ו-Iterator מותאמות אישית (שתי מחלקות נפרדות)
class FlightScheduleIterator:
   #איטרטור נפרד השומר את מצב המעבר הנוכחי (אינדקס)
    def __init__(self, flights):#הוגדרו כמשתנים פרטיים כדי שלא תהיה אפשרות גישה מבחוץ
        self._flights = flights #רשימת טיסות
        self._index = 0#המצביע על הטיסה

    def __iter__(self):
        return self

    def __next__(self):
        # בדיקה האם הגענו לסוף הרשימה
        if self._index >= len(self._flights):
            raise StopIteration #עצירת הלולאה הגענו לסוף כמות הטיסות ברשימה
        current_flight = self._flights[self._index]
        self._index += 1
        return current_flight


class FlightSchedule:
    #מחלקת אוסף (Iterable) שמחזיקה את לוח הטיסות
    def __init__(self):
        self._flights = [] #רשימה ריקה של טיסות

    def add_flight(self, flight):
        self._flights.append(flight)

    def __iter__(self):
        # כל קריאה יוצרת איטרטור חדש ועצמאי לחלוטין
        return FlightScheduleIterator(self._flights)

# Generator עם yield (סינון כרטיסי טיסה העומדים בתנאי עסקי)
def active_business_tickets_generator(tickets):#מקבלת רשימת כרטיסים
    for ticket in tickets:#עוברת על כל כרטיס ברשימת כרטיסים
        if ticket.get_boarding_priority() == 1:#בודקת אם הכרטיס שייך למחלקת עסקים לפי עדיפות 1
            yield ticket#תמסור את הכרטיס ותעצור בדיוק במיקום של הכרטיס שהייתה בו - תרדמת


# צינור עיבוד עצל (Lazy Pipeline) באמצעות Generator Expressions
def run_lazy_ticket_pipeline(tickets):
    for t in tickets:
        # שלב 1: סינון לפי תנאי ראשון (מחיר בסיס מ-500 ומעלה)
        if t.base_price >= 500:
            # שלב 2: המרה וחישוב מחיר סופי לכרטיס שעבר
            final_price = t.calculate_final_price()
            ticket_id = t.ticket_id
            # שלב 3: הפקת שדה מסכם (טקסט עם מזהה הכרטיס והמחיר)
            summary_text = f"Ticket {ticket_id}: Final Price {final_price}"
            # מוציאים תוצאה אחת בלבד ועוצרים לנוח! כדי שלא ימשיך לרוץ בלולאה
            yield summary_text