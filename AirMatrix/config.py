# config.py - הגדרות המערכת נטענות ממשתני סביבה (ומקובץ .env אם קיים)
# אין כאן סודות: Open-Meteo לא דורש מפתח. קובץ .env לא עולה ל-GitHub (מופיע ב-.gitignore),
# ובמאגר יש רק .env.example עם שמות המשתנים וערכי דוגמה.
import os


def load_env_file(path=".env"):
    # קריאה פשוטה של שורות KEY=VALUE לתוך os.environ.
    # משתנה שכבר הוגדר בסביבה לא נדרס (setdefault), כך שאפשר תמיד לעקוף מבחוץ.
    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue  # שורה ריקה / הערה / שורה לא תקינה
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
    except FileNotFoundError:
        pass  # אין קובץ .env - משתמשים בערכי ברירת המחדל


class AppConfig:#מרכזת את כל ההגדרות במקום אחד ומעבירה אותן לרכיבים מבחוץ
    def __init__(self, weather_base_url, http_timeout, max_attempts, retry_delay_seconds, use_live_api):
        self.weather_base_url = weather_base_url
        self.http_timeout = http_timeout
        self.max_attempts = max_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.use_live_api = use_live_api  # False = הרצת ברירת מחדל ללא רשת (נתונים מדומים)

    @classmethod
    def from_env(cls):#בנאי אלטרנטיבי: בונה את ההגדרות מתוך משתני הסביבה
        load_env_file()
        return cls(
            weather_base_url=os.getenv("AIRMATRIX_WEATHER_URL", "https://api.open-meteo.com/v1/forecast"),
            http_timeout=float(os.getenv("AIRMATRIX_HTTP_TIMEOUT", "5")),
            max_attempts=int(os.getenv("AIRMATRIX_MAX_ATTEMPTS", "3")),
            retry_delay_seconds=float(os.getenv("AIRMATRIX_RETRY_DELAY", "1")),
            use_live_api=os.getenv("AIRMATRIX_USE_LIVE_API", "false").lower() in ("1", "true", "yes"),
        )
