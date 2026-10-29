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


# ---------- שלב 2: הצגת תוצאות בדיקת מזג האוויר בעברית ----------
CATEGORY_NAMES = {"PET": "בעל חיים", "PERISHABLE": "מזון מתכלה"}


def format_weather_check(result):
    # מחזירה רשימת שורות טקסט לתוצאת בדיקה של טיסה אחת (ההדפסה עצמה נעשית ב-main)
    header = f"טיסה {result.flight_number} ליעד {result.destination_city} ({result.destination})"
    lines = []

    if result.status == "MANUAL_CHECK":
        lines.append(f"{header}: שירות מזג האוויר לא זמין - לא בוצע עדכון אוטומטי, נדרשת בדיקה ידנית")
        return lines

    if result.weather is None:
        lines.append(f"{header}: אין מטען רגיש בטיסה - לא נדרשה בדיקת מזג אוויר")
        return lines

    source = "מדומה" if result.weather.is_simulated else "אמיתי"
    decision = "עוכב מטען רגיש" if result.status == "HOLD" else "כל המטען הרגיש אושר להטסה"
    lines.append(f"{header}: {decision}")
    lines.append(f"    מזג אוויר ביעד: {result.weather.temperature_c}°C, רוח {result.weather.wind_speed_kmh} קמ\"ש"
                 f" (נתון {source})")
    lines.append(f"    עוכבו: {len(result.held_items)} | אושרו: {len(result.cleared_items)}")
    for item in result.held_items:
        lines.append(f"    מעוכב: {item.baggage_id} - {CATEGORY_NAMES[item.cargo_category]}, {item.weight_kg} ק\"ג")
    for item in result.cleared_items:
        lines.append(f"    אושר: {item.baggage_id} - {CATEGORY_NAMES[item.cargo_category]}, {item.weight_kg} ק\"ג")
    return lines


def format_incident(incident):
    status = "פתוחה" if incident.status == "OPEN" else "סגורה"
    return (f"פנייה {incident.incident_id} ({status}) | טיסה {incident.flight_number} | "
            f"מטען {incident.baggage_id} | סיבה: {incident.reason}")
