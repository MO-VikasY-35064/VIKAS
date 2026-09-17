from pathlib import Path
from flask import Flask, send_from_directory, jsonify, url_for

from config import Config
from . import db as db_module
from .utils import inr, ALL_ORDER_STATUSES


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)

    Path(app.config["UPLOAD_ROOT"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["LOG_DIR"]).mkdir(parents=True, exist_ok=True)

    db_module.init_db(app)
    _seed_demo_data(app)

    # Blueprints
    from .auth import bp as auth_bp
    from .public import bp as public_bp
    from .customer import bp as customer_bp
    from .admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(customer_bp, url_prefix="/customer")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Serve uploaded images (BRS Section 3) - in production IIS/nginx
    # would normally serve this folder directly & more efficiently.
    @app.route("/media/<path:filename>")
    def media(filename):
        return send_from_directory(app.config["UPLOAD_ROOT"], filename)

    # --------------------------------------------------------------
    # PWA support: manifest (dynamic, so it reflects the brand name set
    # in Admin > Settings) + service worker served from the site root
    # so its cache scope covers the whole app.
    # --------------------------------------------------------------
    @app.route("/manifest.webmanifest")
    def manifest():
        rows = db_module.query("SELECT setting_key, setting_value FROM website_settings")
        settings = {r["setting_key"]: r["setting_value"] for r in rows}
        brand = settings.get("brand_name") or "Tailoring Studio"
        manifest_json = {
            "name": brand,
            "short_name": brand[:12],
            "description": settings.get("about_us") or "Custom blouse tailoring, ordering and tracking.",
            "start_url": "/?source=pwa",
            "scope": "/",
            "display": "standalone",
            "orientation": "portrait",
            "background_color": "#faf6f0",
            "theme_color": "#4c1520",
            "icons": [
                {"src": url_for("static", filename="icons/icon-192.png"), "sizes": "192x192",
                 "type": "image/png", "purpose": "any"},
                {"src": url_for("static", filename="icons/icon-512.png"), "sizes": "512x512",
                 "type": "image/png", "purpose": "any"},
                {"src": url_for("static", filename="icons/icon-512-maskable.png"), "sizes": "512x512",
                 "type": "image/png", "purpose": "maskable"},
            ],
        }
        response = jsonify(manifest_json)
        response.headers["Content-Type"] = "application/manifest+json"
        return response

    @app.route("/sw.js")
    def service_worker():
        # Served from root (not /static/) so its default scope is "/",
        # letting it control every page, not just /static/*.
        response = send_from_directory(app.static_folder, "js/sw.js")
        response.headers["Content-Type"] = "application/javascript"
        response.headers["Service-Worker-Allowed"] = "/"
        return response

    app.jinja_env.filters["inr"] = inr
    app.jinja_env.filters["datestr"] = lambda v: str(v)[:10] if v else ""
    app.jinja_env.globals["ALL_ORDER_STATUSES"] = ALL_ORDER_STATUSES

    @app.context_processor
    def inject_settings():
        from . import db
        rows = db.query("SELECT setting_key, setting_value FROM website_settings")
        settings = {r["setting_key"]: r["setting_value"] for r in rows}
        return {"site": settings}

    return app


def _seed_demo_data(app):
    """Populate a couple of demo rows on first run so the app is usable
    immediately (a default admin login + sample designs + settings)."""
    from werkzeug.security import generate_password_hash

    with app.app_context():
        admin_count = db_module.query("SELECT COUNT(*) c FROM admin_users", one=True)["c"]
        if admin_count == 0:
            db_module.execute(
                "INSERT INTO admin_users (username, password_hash, full_name) VALUES (?, ?, ?)",
                ("admin", generate_password_hash("admin123"), "Administrator"),
            )
            app.logger.info("Seeded default admin user: admin / admin123 (CHANGE THIS PASSWORD)")

        settings_count = db_module.query("SELECT COUNT(*) c FROM website_settings", one=True)["c"]
        if settings_count == 0:
            defaults = {
                "brand_name": "Elegance Blouse Tailors",
                "about_us": "Custom blouse tailoring with a modern touch - precise measurements, "
                             "premium finish, and a smooth online ordering experience.",
                "address": "12 Tailor Street, Hyderabad, Telangana",
                "contact_number": "+91 90000 00000",
                "contact_email": "hello@elegance-tailors.example",
            }
            for k, v in defaults.items():
                db_module.execute(
                    "INSERT INTO website_settings (setting_key, setting_value) VALUES (?, ?)",
                    (k, v),
                )

        design_count = db_module.query("SELECT COUNT(*) c FROM designs", one=True)["c"]
        if design_count == 0:
            sample_designs = [
                ("Royal V-Neck", "Elegant V-neck blouse with piping detail.", "Party Wear",
                 "V-Neck", "Elbow Sleeve", "Regular", "Piping, Latkans available", 1200, 200, "ACTIVE"),
                ("Classic Boat Neck", "Timeless boat neck design for everyday elegance.", "Traditional",
                 "Boat Neck", "Sleeveless", "Regular", "Lining optional", 900, 0, "ACTIVE"),
                ("Bridal Zardozi", "Heavy zardozi work blouse for weddings.", "Bridal",
                 "Deep V", "Full Sleeve", "Long", "Zardozi, Stone work, Lining included", 3500, 800, "ACTIVE"),
                ("Simple Cotton Fit", "Comfortable everyday cotton blouse.", "Simple",
                 "Round Neck", "Short Sleeve", "Regular", "None", 500, 0, "ACTIVE"),
            ]
            for d in sample_designs:
                db_module.execute(
                    """INSERT INTO designs
                       (name, description, category, neck_style, sleeve_style, blouse_length,
                        customisation_details, base_price, additional_charges, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    d,
                )
