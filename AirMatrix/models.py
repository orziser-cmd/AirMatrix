from abc import ABC, abstractmethod


class Passenger:
    """מייצגת נוסע במערכת ומנהלת את פרטי הזיהוי שלו"""

    def __init__(self, passenger_id, full_name, passport_number):#בנאי בסיסי של המחלקה נוסע
        self.passenger_id = passenger_id
        self.full_name = full_name
        self.passport_number = passport_number

    @classmethod
    def from_line(cls, line_str):
        # פיצול השורה לפי פסיקים
        parts = line_str.split(",")
        passenger_id = parts[0].strip()
        full_name = parts[1].strip()
        passport_number = parts[2].strip()
        return cls(passenger_id, full_name, passport_number)

    def __str__(self):#מויעדת למשתמש הקצה בתצוגה
        return f"Full Name:{self.full_name} | Passport: {self.passport_number}"

    def __repr__(self):#ייצוג מתודי במערכת
        return f"Passenger(passenger_id='{self.passenger_id}', full_name='{self.full_name}', passport_number='{self.passport_number}')"

    def __eq__(self, other):#בדיקה ששני נוסעים שונים באותו שם לא יהיו עם אותה ת.ז כי זה משתנה ייחודי
        if isinstance(other, Passenger):
            return self.passenger_id == other.passenger_id
        return False

    def __hash__(self):
        return hash(self.passenger_id)


class Ticket(ABC):
    """מחלקת בסיס אבסטרקטית מייצגת את הכרטיס טיסה"""

    def __init__(self, ticket_id, passenger, flight_number, base_price, seat_number, status="CONFIRMED"):
        self.ticket_id = ticket_id
        self.passenger = passenger #אובייקט מסוג מחלקת נוסע
        self.flight_number = flight_number
        self.base_price = base_price
        self.seat_number = seat_number
        self.status = status

    @abstractmethod
    def calculate_final_price(self, extra_bags=0):
        pass

    @abstractmethod
    def get_boarding_priority(self):
        pass

    @classmethod
    def from_line(cls, line_str, passenger_obj):
        # פיצול השורה לפי פסיקים
        parts = line_str.split(",")
        ticket_id = parts[0].strip()
        flight_number = parts[1].strip()
        base_price = float(parts[2].strip())
        seat_number = parts[3].strip()
        return cls(ticket_id, passenger_obj, flight_number, base_price, seat_number)

    def __str__(self):
        return f"Ticket #{self.ticket_id} [{self.seat_number}] | {self.passenger.full_name}"

    def __repr__(self):
        return f"Ticket(ticket_id={self.ticket_id}, flight_number={self.flight_number}, seat_number={self.seat_number})"

    def __lt__(self, other):
        return self.get_boarding_priority() < other.get_boarding_priority()


class EconomyTicket(Ticket):#יורשת ממחלקת בסיס
    """מייצגת כרטיס טיסה במחלקת תיירים"""

    def __init__(self, ticket_id, passenger, flight_number, base_price, seat_number,baggage_fee=45.0, status="CONFIRMED"):
        super().__init__(ticket_id, passenger, flight_number, base_price, seat_number, status)
        self.baggage_fee = baggage_fee

    def calculate_final_price(self, extra_bags=0):
        if extra_bags < 0:
            raise ValueError("Extra bags cannot be negative")
        return self.base_price + (extra_bags * self.baggage_fee)

    def get_boarding_priority(self):
        return 2

    def __str__(self):
        return f"Economy Ticket #{self.ticket_id} [Seat: {self.seat_number}] | {self.passenger.full_name}"

    def __repr__(self):
        return f"Economy Ticket(ticket_id={self.ticket_id}, flight_number={self.flight_number}, seat_number={self.seat_number})"


class BusinessTicket(Ticket):#יורשת ממחלקת בסיס כרטיס
    """מייצגת כרטיס טיסה במחלקת עסקים"""
    def __init__(self, ticket_id, passenger, flight_number, base_price, seat_number, status="CONFIRMED", includes_lounge=True,lounge_fee=35.0):
        super().__init__(ticket_id, passenger, flight_number, base_price, seat_number, status)
        self.includes_lounge = includes_lounge
        self.lounge_fee = lounge_fee

    def calculate_final_price(self, extra_bags=0):
        if extra_bags < 0:
            raise ValueError("Extra bags cannot be negative")

        # במחלקת עסקים מזוודה אחת כלולה בכרטיס בחינם
        if extra_bags > 1:
            extra_cost = (extra_bags - 1) * 25.0
        else:
            extra_cost = 0.0

        total = self.base_price + extra_cost

        if self.includes_lounge:
            total += self.lounge_fee

        return total

    def get_boarding_priority(self):
        return 1

    def __str__(self):
        return f"Business Ticket #{self.ticket_id} [Seat: {self.seat_number}] | {self.passenger.full_name}"

    def __repr__(self):
        return f"Business Ticket(ticket_id={self.ticket_id}, flight_number={self.flight_number}, seat_number={self.seat_number})"

class Flight:#  מייצגת טיסה במערכת
    def __init__(self, flight_number, origin, destination, capacity):
        self.flight_number = flight_number
        self.origin = origin
        self.destination = destination
        self.capacity = capacity
        self.tickets = [] #רשימה של אובייקטים מסוג כרטיס - הרכבה

    @property
    def capacity(self):#GETTER
        return self._capacity

    @capacity.setter
    def capacity(self, value):
        if value <= 0:
            raise ValueError("Capacity must be a positive number")
        self._capacity = value

    @classmethod
    def from_line(cls, line_str):
        # פיצול השורה לפי פסיקים וניקוי רווחים
        parts = line_str.split(",")
        flight_number = parts[0].strip()
        origin = parts[1].strip()
        destination = parts[2].strip()
        capacity = int(parts[3].strip())
        return cls(flight_number, origin, destination, capacity)

    def add_ticket(self, ticket):
        if len(self.tickets) >= self.capacity:
            raise ValueError(f"Flight {self.flight_number} is fully booked")
        self.tickets.append(ticket)

    def get_total_revenue(self):#שימוש בפולימורפיזם
        total = 0.0
        for ticket in self.tickets:
            total += ticket.calculate_final_price()#בודק לפי סוג הכרטיס לאיזה מחלקה משויך ומחשב בהתאמה
        return total

    def __len__(self):
        return len(self.tickets)

    def __str__(self):
        return f"Flight {self.flight_number}: {self.origin} -> {self.destination} ({len(self.tickets)}/{self.capacity} seats)"

    def __repr__(self):
        return f"Flight(flight_number={self.flight_number}, origin={self.origin}, destination={self.destination}, capacity={self.capacity})"


# הרחבה של 2 מחלקות בגלל שאנחנו קבוצה של 4

class BaggageItem:
    """מייצגת פריט כבודה בודד של נוסע עם מעקב מצבים"""

    def __init__(self, baggage_id, ticket_id, weight_kg, status="CHECKED_IN"):
        self.baggage_id = baggage_id
        self.ticket_id = ticket_id
        self.weight_kg = weight_kg
        self.status = status  # מצבים אפשריים: CHECKED_IN -> SCREENED -> LOADED

    def pass_security(self):
        """מעבירה את המזוודה בדיקה ביטחונית"""
        if self.status != "CHECKED_IN":
            raise ValueError("Only checked-in bags can pass security screening")
        self.status = "SCREENED"

    def mark_as_loaded(self):
        """מעדכנת שהמזוודה הועמסה למטוס (תוצאה סופית של התהליך)"""
        if self.status != "SCREENED":
            raise ValueError("Bag cannot be loaded before passing security screening")
        self.status = "LOADED"

    def __str__(self):
        return f"Bag #{self.baggage_id} (Ticket: {self.ticket_id}) - {self.weight_kg}kg [{self.status}]"

    def __repr__(self):
        return f"Baggage Item(baggage_id={self.baggage_id}, ticket_id={self.ticket_id}, weight_kg={self.weight_kg}, status={self.status})"


class BaggageManifest:
    """מנהלת את ריכוז המטען של טיסה ומכילה את הפעולות העסקיות להרחבה"""

    def __init__(self, flight_number, max_total_weight_kg=3500.0):
        self.flight_number = flight_number
        self.max_total_weight_kg = max_total_weight_kg
        self.items = [] #רשימה של מטעני כבודה - הרכבה

    def get_total_weight(self):#מתודת חישוב משקל
        total = 0.0
        for item in self.items:
            total += item.weight_kg
        return total

    # --- פעולה עסקית 1: העמסה מבוקרת (חלק מסיום התהליך) ---
    def load_bag(self, baggage_item):
        current_weight = self.get_total_weight()
        if current_weight + baggage_item.weight_kg > self.max_total_weight_kg:
            raise ValueError(f"Adding bag {baggage_item.baggage_id}is over the weight limit")

        # מעבירים את המזוודה למצב סופי LOADED (יזרוק ValueError אם לא עברה בידוק)
        baggage_item.mark_as_loaded()
        self.items.append(baggage_item)

    # --- פעולה עסקית 2: סינון מזוודות חריגות משקל ---
    def get_overweight_bags(self, threshold_kg=23.0):
        overweight_list = [] #רשימה של מזוודות כבדות משקל חריגות
        for bag in self.items:
            if bag.weight_kg > threshold_kg:
                overweight_list.append(bag)
        return overweight_list

    # --- פעולה עסקית 3: דוח תפוסת משקל והתרעות למטוס ---
    def get_capacity_summary(self):
        total_weight = self.get_total_weight()
        remaining_capacity = self.max_total_weight_kg - total_weight
        usage_percent = (total_weight / self.max_total_weight_kg) * 100

        if usage_percent >= 90.0:
            warning_level = "CRITICAL"
        else:
            warning_level = "NORMAL"

        return {
            "total_weight": total_weight,
            "remaining_capacity": remaining_capacity,
            "usage_percent": round(usage_percent, 1),
            "warning_level": warning_level
        }

    def __len__(self):#מספר מזוודות
        return len(self.items)

    def __str__(self):
        return f"Manifest for Flight {self.flight_number}: {len(self.items)} bags, Total: {self.get_total_weight()}kg/{self.max_total_weight_kg}kg"

    def __repr__(self):
        return f"BaggageManifest(flight_number={self.flight_number}, count={len(self.items)}, total_weight={self.get_total_weight()})"