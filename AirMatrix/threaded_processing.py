# threaded_processing.py - Threads ומשאב משותף (סעיף 5.2)
# התרחיש: לבעלי חיים יש מספר מוגבל של מקומות בתא המבוקר טמפרטורה בבטן המטוס.
# כמה דלפקי צ'ק-אין (Threads) מנסים בו-זמנית לשריין את המקום האחרון.
#
# למה צריך Lock? השריון הוא "בדיקה ואז עדכון":
#   1. בודקים אם נשאר מקום   2. מוסיפים את הכלוב לרשימה
# בלי נעילה ייתכן הסדר הבא: דלפק א' בודק -> נשאר מקום אחד; לפני שהוא מעדכן, מערכת ההפעלה
# עוברת לדלפק ב', שגם הוא בודק -> עדיין נשאר מקום אחד (כי א' עוד לא עדכן). שניהם מוסיפים,
# וקיבלנו 2 בעלי חיים על מקום אחד (Overbooking). ה-Lock הופך את שני הצעדים לפעולה אחת
# שרק Thread אחד יכול לבצע בכל רגע.
import threading


class PetHoldCapacity:#המשאב המשותף: מקומות בתא בעלי החיים בטיסה אחת
    def __init__(self, flight_number, total_slots):
        if total_slots <= 0:
            raise ValueError("Pet hold must have at least one slot")
        self.flight_number = flight_number
        self.total_slots = total_slots
        self.reserved = []             # מזהי הכלובים ששוריינו
        self._lock = threading.Lock()  # אותו Lock לכל הדלפקים

    def available_slots(self):
        with self._lock:
            return self.total_slots - len(self.reserved)

    def reserve(self, baggage_id):
        # כל רצף הבדיקה והעדכון נמצא בתוך הנעילה. אין כאן קריאות רשת - הנעילה קצרה ככל האפשר
        with self._lock:
            if len(self.reserved) >= self.total_slots:
                return False
            self.reserved.append(baggage_id)
            return True


def run_checkin_counters(capacity, baggage_ids):
    # כל כלוב מטופל ב-Thread נפרד (דלפק). Barrier גורם לכולם להגיע לשריון באותו רגע,
    # כדי ליצור תחרות אמיתית על המשאב.
    barrier = threading.Barrier(len(baggage_ids))
    outcomes = {}                      # baggage_id -> True/False
    outcomes_lock = threading.Lock()   # גם מילון התוצאות משותף לכל ה-Threads

    def counter_worker(baggage_id):
        barrier.wait()
        approved = capacity.reserve(baggage_id)
        with outcomes_lock:
            outcomes[baggage_id] = approved

    threads = [threading.Thread(target=counter_worker, args=(bag_id,), name=f"counter-{bag_id}")
               for bag_id in baggage_ids]
    for thread in threads:  # קודם מפעילים את כולם...
        thread.start()
    for thread in threads:  # ...ורק אחר כך ממתינים לסיום (join)
        thread.join()
    return outcomes
