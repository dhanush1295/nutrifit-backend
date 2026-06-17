import os

class Config:
    # MySQL
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "12345678")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "nutrifit")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "nutrifit-secret-key-change-in-production-2026")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24 * 30  # 30 days

    # OpenRouter (for Coach AI proxy)
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = "google/gemma-4-31b-it:free"

    # SMTP for Email Sending
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "nutrifitsupportsimats@gmail.com")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

    # Allowed email domain suffixes for sign-up and sign-in
    ALLOWED_EMAIL_DOMAINS = [
        "gmail.com",
        "yahoo.com",
        "yahoo.in",
        "yahoo.co.in",
        "outlook.com",
        "hotmail.com",
        "icloud.com",
        "protonmail.com",
        "rediffmail.com",
        "aol.com",
        "live.com",
        "msn.com",
        "mail.com",
        "zoho.com",
        "yandex.com",
    ]

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email has correct format and an allowed domain suffix."""
        if not email or "@" not in email:
            return False
        parts = email.strip().lower().split("@")
        if len(parts) != 2:
            return False
        local, domain = parts
        if not local or not domain:
            return False
        if "." not in domain:
            return False
        return domain in Config.ALLOWED_EMAIL_DOMAINS
