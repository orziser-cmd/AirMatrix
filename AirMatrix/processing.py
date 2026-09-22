from collections import deque
import heapq

#חלק ג' - מבני נתונים ואוספים
def demonstrate_list_and_tuples(flights):
    #רשימה (list): אוסף טיסות הניתן לשינוי
    #טאפל (tuple): רשומה קבועה וקצרה של תמצית טיסה (flight_number, origin, destination)
    flight_records = [] #מקבל רשימת טיסות ויוצר רשימה חדשה
    for f in flights:#עובר בלולאה ומכניס את הטיסות לטאפל
        record = (f.flight_number, f.origin, f.destination)
        flight_records.append(record)

    # שימוש ב-* לפריקת שורת נתונים המכילה ערכים נוספים
    sample_raw_record = ["AM101", "TLV", "JFK", "Terminal 3", "Gate B4", "On Schedule"]
    flight_id, src, dst, *extra_airport_details = sample_raw_record

    return flight_records, extra_airport_details

#set (ערכים ייחודיים, פעולות קבוצתיות ואימות)
def demonstrate_sets(all_tickets, cancelled_ticket_ids):
    #שימוש ב-set לשמירת מזהים ייחודיים ובדיקות קבוצתיות
    #הערכים הם מחרוזות (hashable)
    active_ticket_ids = set()# יצירת קבוצת כל מזהי הכרטיסים
    for ticket in all_tickets: #טיפוס שהוא מחרוזת טקסט ולכן הוא האשבל כי הוא אימיוטיבל
        active_ticket_ids.add(ticket.ticket_id)  #  add - הוספת מזהה כרטיס חדש
    #  בדיקת השתייכות באמצעות in
    is_valid = "T101" in active_ticket_ids
    return active_ticket_ids, is_valid

# dict (שני מילונים, get, איטרציית items עם unpacking ומניעת כפילות)
def build_tickets_by_id(tickets_list):
    #מילון 1: איתור אובייקט כרטיס לפי מזהה ייחודי (טיפול בכפילות מזהים)
    tickets_dict = {} #מילון של כרטיסים
    for ticket in tickets_list:
        if ticket.ticket_id in tickets_dict:#בודק כפילות של מזהה כרטיס
            raise ValueError(f"Duplicate ticket ID found: {ticket.ticket_id}")#הערה שהוא כבר קיים במילון
        tickets_dict[ticket.ticket_id] = ticket
    return tickets_dict

def group_tickets_by_passenger(tickets_list):
    #מילון 2: קיבוץ רשימת כרטיסים לפי מזהה נוסע (כולל שימוש ב-get ו-items)
    passenger_tickets = {} #מילון של כרטיסי נוסעים
    for ticket in tickets_list:
        p_id = ticket.passenger.passenger_id
        # get עם ערך ברירת מחדל של רשימה ריקה כאשר המפתח טרם קיים
        current_list = passenger_tickets.get(p_id, [])
        current_list.append(ticket)
        passenger_tickets[p_id] = current_list

    # מעבר על המילון באמצעות items() ו-unpacking
    summary = {}#מילון שמסכם את מספר הכרטיסים
    for passenger_id, tickets in passenger_tickets.items():
        summary[passenger_id] = len(tickets)

    return passenger_tickets, summary

# תור FIFO באמצעות deque (עמדת צ'ק-אין / בידוק ביטחוני)
def process_security_queue(baggage_items):
    #סדר ההגעה קריטי: הוגנות שירות (First-Come, First-Served) בבידוק הביטחוני
    #מזוודה שהגיעה ראשונה לדלפק נבדקת ומאושרת ראשונה
    security_queue = deque()#יצירת תור חדש

    # הוספת פריטים לסוף התור
    for bag in baggage_items:
        security_queue.append(bag)

    processed_bags = []
    # שליפת פריטים מתחילת התור תוך טיפול בטוח בתור ריק
    while security_queue:#יעבור ויכנס ללולאה כל עוד אינו ריק
        try:
            current_bag = security_queue.popleft()
            current_bag.pass_security()
            processed_bags.append(current_bag)
        except IndexError:
            break

    return processed_bags

#  תור עדיפויות באמצעות heapq (עלייה למטוס - Boarding)
def process_boarding_priority_queue(tickets):
    #תור עדיפויות: דחיפות קודמת לזמן ההגעה
    #המספר הקטן מציין עדיפות גבוהה יותר (1 - עסקים, 2 - תיירים)
    #שוויון נפתר בצורה דטרמיניסטית ע"י ticket_id כדי לא להסתמך על השוואת אובייקטים מעורפלת
    priority_queue = []
    # הכנסת פריטים ל-heap (עדיפות, מזהה שובר שוויון, אובייקט)
    for ticket in tickets:
        priority = ticket.get_boarding_priority()
        # מבנה הטאפל מבטיח שוויון יציב: (priority, ticket_id, ticket)
        item = (priority, ticket.ticket_id, ticket)#השוואה גם של עדיפות ומספר כרטיס
        heapq.heappush(priority_queue, item)#שולף אוטומטית את האיבר בעל הערך הנמוך ביותר בעדיפות - קודם את 1

    boarding_order = []
    while priority_queue:
        priority, _, current_ticket = heapq.heappop(priority_queue)#שליפת האיבר בעל העדיפות הגבוהה ביותר - מספר נמוך יותר
        boarding_order.append(current_ticket)

    return boarding_order

#Comprehensions (List, Set, Dict)
def demonstrate_comprehensions(tickets):
    # 1. List Comprehension: סינון והמרה - רשימת מחירי כרטיסים סופיים בלבד
    ticket_prices = [t.calculate_final_price() for t in tickets]

    # 2. Set Comprehension: הפקת יעדי טיסה ייחודיים מכלל הכרטיסים
    unique_flight_numbers = {t.flight_number for t in tickets}

    # 3. Dict Comprehension: אינדוקס מזהה כרטיס למספר המושב שלו
    seat_mapping = {t.ticket_id: t.seat_number for t in tickets}

    return ticket_prices, unique_flight_numbers, seat_mapping

# מיון ופונקציות כערכים (sorted, key, lambda, tuple)
def get_ticket_base_price(ticket):
    #פונקציה רגילה המשמשת כ-key למיון
    return ticket.base_price

def demonstrate_sorting(tickets):
    # 1. מיון באמצעות פונקציה רגילה כ-key: מיון לפי מחיר בסיס מהנמוך לגבוה
    by_price = sorted(tickets, key=get_ticket_base_price)

    # 2. מיון באמצעות lambda קצרה כ-key: מיון לפי מספר מושב
    by_seat = sorted(tickets, key=lambda t: t.seat_number)

    # 3. מיון לפי שני שדות באמצעות tuple: קודם לפי קדימות עלייה, ובתוך כל עדיפות לפי מחיר יורד
    by_priority_and_price = sorted(tickets,key=lambda t: (t.get_boarding_priority(), -t.calculate_final_price()))#שמנו מינוס כדי להפוך את המחיר

    return by_price, by_seat, by_priority_and_price