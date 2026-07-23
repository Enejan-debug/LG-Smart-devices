import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    # ---- Secret key for session cookies (admin login state) ----
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-this-in-production")

    # ---- Database ----
    # By default this uses a local SQLite file (lgstore.db) so the project
    # runs immediately with zero setup - no MySQL server required.
    #
    # If you want to use MySQL instead (like the original Java project),
    # comment out the SQLite line below and uncomment + edit the MySQL line.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'lgstore.db')}"
    )

    # Example MySQL connection string (requires: pip install pymysql):
    # SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:your_password@localhost:3306/lgstore"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- File uploads (profile photos) ----
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload size

    # ---- Admin credentials ----
    # Matches the original project's hardcoded admin/admin123 for course purposes.
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

    # ---- Store / seller contact info ----
    # Single physical store, shown on every product page so customers can
    # call or visit before paying (cash on pickup or phone/bank transfer).
    STORE_INFO = {
        "name": "LG Store - Idris",
        "address": "Yoloten şäher, Mary welayaty, Türkmenistan",
        "phone": "+993 61 770075",
        "email": "contact@lgstore.example.com",
        "hours": "Mon-Sat, 9:00 AM - 8:00 PM",
    }
