# strategies.py - תבנית Strategy: דרכים חלופיות לחישוב עמלת טיפול בכבודה
# לכל האסטרטגיות יש אותו חוזה (calculate_fee), והמזוודה רק "מחזיקה" אסטרטגיה ומפעילה אותה.
# כך אפשר להחליף את שיטת החישוב (למשל מדיניות עונתית) בלי לשנות את מחלקת המזוודה,
# ולבדוק כל שיטת חישוב בנפרד.
from abc import ABC, abstractmethod


class BaggageFeeStrategy(ABC):#"ממשק" - חוזה בלבד, בלי לוגיקה משותפת
    @abstractmethod
    def calculate_fee(self, weight_kg):
        """מחזירה את עמלת הטיפול בש"ח עבור פריט במשקל הנתון."""

    @abstractmethod
    def describe(self):
        """תיאור קצר של המדיניות, לצורך דוחות."""


class StandardBaggageFee(BaggageFeeStrategy):#כבודה רגילה: חינם עד המשקל המותר, תשלום לכל ק"ג חריג
    def __init__(self, free_allowance_kg=23.0, price_per_extra_kg=12.0):
        self.free_allowance_kg = free_allowance_kg
        self.price_per_extra_kg = price_per_extra_kg

    def calculate_fee(self, weight_kg):
        extra_kg = max(0.0, weight_kg - self.free_allowance_kg)
        return round(extra_kg * self.price_per_extra_kg, 2)

    def describe(self):
        return f"Standard: free up to {self.free_allowance_kg}kg, {self.price_per_extra_kg} per extra kg"


class SpecialCargoFee(BaggageFeeStrategy):#מטען רגיש / בעלי חיים: עמלת טיפול קבועה (תא מבוקר טמפרטורה) + תשלום לפי ק"ג
    def __init__(self, handling_fee=150.0, price_per_kg=8.0):
        self.handling_fee = handling_fee
        self.price_per_kg = price_per_kg

    def calculate_fee(self, weight_kg):
        return round(self.handling_fee + weight_kg * self.price_per_kg, 2)

    def describe(self):
        return f"Special cargo: {self.handling_fee} handling + {self.price_per_kg} per kg"
