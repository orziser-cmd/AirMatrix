# מודול reports.py - הפקת דוחות  למערכת
def generate_flight_revenue_report(flight):
    # דוח להצגת הכנסות ופרטי טיסה
    total_revenue = flight.get_total_revenue()
    print("========================================")
    print("דוח הכנסות לטיסה:", flight.flight_number)
    print("מוצא:", flight.origin, "| יעד:", flight.destination)
    print("קיבולת מושבים:", flight.capacity)
    print("הכנסה כוללת מנוסעים:", total_revenue)
    print("========================================")

def generate_passenger_summary_report(tickets_list):
    # דוח לספירת כרטיסים לכל נוסע בעזרת מילון ולולאה רגילה
    passenger_counts = {}
    for ticket in tickets_list:
        p_id = ticket.passenger.passenger_id
        # אם הנוסע כבר קיים במילון, נוסיף 1, אם לא - נגדיר ל-1
        if p_id in passenger_counts:
            passenger_counts[p_id] = passenger_counts[p_id] + 1
        else:
            passenger_counts[p_id] = 1

    print("----------------------------------------")
    print("סיכום כרטיסים לפי נוסע")
    print("----------------------------------------")

    # מעבר על המילון והדפסה
    for p_id in passenger_counts:
        count = passenger_counts[p_id]
        print("מזהה נוסע:", p_id, "| כמות כרטיסים:", count)

    print("----------------------------------------")


def generate_baggage_manifest_report(baggage_manifest):
    # דוח לתפוסת משקל המזוודות
    summary = baggage_manifest.get_capacity_summary()
    print("****************************************")
    print("דוח כבודה לטיסה:", baggage_manifest.flight_number)
    print("משקל כולל בקילוגרם:", summary["total_weight"])
    print("משקל מקסימלי מותר:", baggage_manifest.max_total_weight_kg)
    print("אחוז תפוסה:", summary["usage_percent"], "%")
    print("רמת עומס:", summary["warning_level"])
    print("****************************************")