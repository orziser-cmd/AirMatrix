class TemporaryDiscount:#בדיקת הנחה זמנית על כרטיס טיסה
    def __init__(self, ticket, discount_amount):
        self.ticket = ticket
        self.discount_amount = discount_amount
        self.original_price = 0

    def __enter__(self):
        # 1. שמירת המחיר המקורי
        self.original_price = self.ticket.base_price

        # 2. עדכון המחיר עם ההנחה
        self.ticket.base_price = self.ticket.base_price - self.discount_amount
        print(f"[ENTER] מחיר זמני עם הנחה: {self.ticket.base_price}")

        # 3. החזרת הכרטיס לשימוש בתוך הבלוק
        return self.ticket

    def __exit__(self, exc_type, exc_val, exc_tb):#סוג שגיאה, תוכן השגיאה, טרייסבאק מאיפה הגיעה
        # שחזור המחיר המקורי
        self.ticket.base_price = self.original_price
        print(f"[EXIT] המחיר הוחזר למקור: {self.ticket.base_price}")
        # לא מסתירים את השגיאה (חריגה תמשיך הלאה אם הייתה)
        return False