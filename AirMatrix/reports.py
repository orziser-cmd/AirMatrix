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


# ---------- שלב 2: דוח משולב (מערכת מרכזית + תת-מערכת הכבודה) ----------
# פותח בשיטת TDD (tests/test_reports.py). אחרי ה-Refactor כל חישוב נמצא בפונקציה קטנה עם שם ברור,
# ו-build_combined_report רק מרכיבה אותם.

def _tickets_for_flight(tickets_by_id, flight_number):#כל הכרטיסים של טיסה אחת (מערכת מרכזית)
    return [ticket for ticket in tickets_by_id.values() if ticket.flight_number == flight_number]


def _held_sensitive_items(items):#מטען רגיש שמעוכב - הבסיס למדד "עמלות בסיכון"
    return [item for item in items if item.is_temperature_sensitive() and item.status.startswith("HELD")]


def _count_open_incidents(incidents, flight_number):
    return sum(1 for incident in incidents if incident.flight_number == flight_number and incident.status == "OPEN")


def _build_flight_row(flight, tickets, items, open_incidents):
    held_sensitive = _held_sensitive_items(items)
    return {
        "destination": flight.destination,
        "passengers": len(tickets),
        "ticket_revenue": sum(ticket.calculate_final_price() for ticket in tickets),  # פולימורפיזם
        "bags": len(items),
        "held_cargo": sum(1 for item in items if item.status.startswith("HELD")),
        "open_incidents": open_incidents,
        # המדד החדש: הכנסה מעמלות שתלויה במטען המעוכב (מחושבת דרך ה-Strategy של כל פריט)
        "cargo_fees_at_risk": round(sum(item.calculate_fee() for item in held_sensitive), 2),
        "affected_passengers": len({item.ticket_id for item in held_sensitive}),
    }


def build_combined_report(flights_by_number, tickets_by_id, manifests, incidents):
    flights = {}
    for flight_number, flight in flights_by_number.items():
        manifest = manifests.get(flight_number)
        items = manifest.items if manifest is not None else []
        flights[flight_number] = _build_flight_row(
            flight,
            _tickets_for_flight(tickets_by_id, flight_number),
            items,
            _count_open_incidents(incidents, flight_number),
        )
    totals = {key: round(sum(row[key] for row in flights.values()), 2)
              for key in ("passengers", "ticket_revenue", "held_cargo", "open_incidents",
                          "cargo_fees_at_risk", "affected_passengers")}
    return {"flights": flights, "totals": totals}


def print_combined_report(report):#הדפסת הדוח המשולב בעברית - טבלה לכל טיסה ושורת סיכום
    print("----------------------------------------------------------------------------------")
    print("טיסה  | יעד | נוסעים | הכנסה מכרטיסים | מזוודות | מעוכבים | פניות פתוחות | עמלות בסיכון")
    print("----------------------------------------------------------------------------------")
    for flight_number, row in sorted(report["flights"].items()):
        print(f"{flight_number} | {row['destination']} | {row['passengers']:>6} | {row['ticket_revenue']:>14.1f} | "
              f"{row['bags']:>7} | {row['held_cargo']:>7} | {row['open_incidents']:>12} | {row['cargo_fees_at_risk']:>11.1f}")
    totals = report["totals"]
    print("----------------------------------------------------------------------------------")
    print(f"סה\"כ: {totals['passengers']} נוסעים, הכנסה {totals['ticket_revenue']:.1f} ₪, "
          f"{totals['open_incidents']} פניות פתוחות")
    print(f"מדד חדש - עמלות מטען בסיכון: {totals['cargo_fees_at_risk']:.1f} ₪ "
          f"({totals['affected_passengers']} נוסעים מושפעים)")

    # תמיכה בהחלטה: הטיסה עם הכי הרבה כסף בסיכון מטופלת ראשונה
    at_risk = [(row["cargo_fees_at_risk"], fn) for fn, row in report["flights"].items() if row["cargo_fees_at_risk"] > 0]
    if at_risk:
        amount, flight_number = max(at_risk)
        print(f"המלצה: לטפל קודם בטיסה {flight_number} ({amount:.1f} ₪ בסיכון)")
