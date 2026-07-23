"""
LG Store - Flask application package.

This package contains ALL backend logic:
- models.py      -> database schema (Product, AdminUser)
- extensions.py  -> shared Flask extension instances (db)
- store_routes.py-> customer-facing routes (public, read-only for the customer)
- admin_routes.py-> developer/admin-only routes (login required, manage products)
- seed.py        -> inserts the starter LG product catalog

The customer NEVER sees backend code - they only ever see the rendered
HTML pages in /templates (store side). Everything under /admin requires
a logged-in admin session, mirroring the original Java project's
"isAdmin" session guard.
"""
from flask import Flask, session
from .extensions import db
from .translations import translate, DEFAULT_LANG, SUPPORTED_LANGS


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config.from_object("backend.config.Config")

    db.init_app(app)

    # ---- Price formatting: show every price in Turkmenistani manat (TMT) ----
    @app.template_filter("tmt")
    def format_tmt(value):
        try:
            return f"{float(value):,.2f} TMT".replace(",", " ")
        except (TypeError, ValueError):
            return f"{value} TMT"

    # ---- Translation helper: {{ t('key') }} available in every template ----
    @app.context_processor
    def inject_translator():
        lang = session.get("lang", DEFAULT_LANG)
        if lang not in SUPPORTED_LANGS:
            lang = DEFAULT_LANG
        return {
            "t": lambda key: translate(key, lang),
            "current_lang": lang,
        }

    # Register blueprints
    from .store_routes import store_bp
    from .admin_routes import admin_bp

    app.register_blueprint(store_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        db.create_all()
        from .seed import seed_if_empty
        seed_if_empty()

    return app
