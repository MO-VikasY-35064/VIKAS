from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .utils import is_valid_mobile, is_valid_email, is_valid_password, write_audit_log

bp = Blueprint("auth", __name__)


# =====================================================================
# Customer registration / login   (BRS Section 6 / 7)
# =====================================================================
@bp.route("/register", methods=["GET", "POST"])
def customer_register():
    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()

        errors = []
        if not is_valid_mobile(mobile):
            errors.append("Enter a valid 10-digit mobile number.")
        if not is_valid_password(password):
            errors.append("Password must be at least 6 characters.")
        if not is_valid_email(email):
            errors.append("Enter a valid email address.")

        existing = db.query("SELECT id FROM customers WHERE mobile = ?", (mobile,), one=True)
        if existing:
            errors.append("This mobile number is already registered. Please login instead.")  # BR-002

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("public/register.html", form=request.form)

        customer_id = db.execute(
            "INSERT INTO customers (mobile, password_hash, name, email) VALUES (?, ?, ?, ?)",
            (mobile, generate_password_hash(password), name or None, email or None),
        )
        session.clear()
        session["customer_id"] = customer_id
        flash("Registration successful! Let's set up your measurements.", "success")
        # Scenario A (BRS Section 7): new customer -> no measurement yet
        return redirect(url_for("customer.measurements", first_time=1))

    return render_template("public/register.html", form={})


@bp.route("/login", methods=["GET", "POST"])
def customer_login():
    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        customer = db.query("SELECT * FROM customers WHERE mobile = ?", (mobile,), one=True)

        if not customer or not check_password_hash(customer["password_hash"], password):
            flash("Invalid mobile number or password.", "danger")
            return render_template("public/login.html")

        if not customer["is_active"]:
            flash("Your account has been deactivated. Please contact us.", "danger")
            return render_template("public/login.html")

        session.clear()
        session["customer_id"] = customer["id"]
        flash(f"Welcome back, {customer['name'] or customer['mobile']}!", "success")

        # Scenario B (BRS Section 7): existing customer, has measurement?
        has_measurement = db.query(
            "SELECT id FROM measurements WHERE customer_id = ? AND is_current = 1",
            (customer["id"],), one=True,
        )
        next_url = request.args.get("next")
        if next_url:
            return redirect(next_url)
        if not has_measurement:
            return redirect(url_for("customer.measurements", first_time=1))
        return redirect(url_for("customer.dashboard"))

    return render_template("public/login.html")


@bp.route("/logout")
def customer_logout():
    session.pop("customer_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("public.home"))


# =====================================================================
# Admin login  (BRS Section 8) - kept fully separate from customer auth
# =====================================================================
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


@bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = db.query("SELECT * FROM admin_users WHERE username = ?", (username,), one=True)

        if admin and admin["locked_until"]:
            # locked_until comes back as a native datetime on MS SQL Server
            # (pyodbc + DATETIME2), but as a string on SQLite - handle both.
            locked_until = admin["locked_until"]
            if isinstance(locked_until, str):
                locked_until = datetime.fromisoformat(locked_until)
            if locked_until > datetime.now():
                flash(f"Account locked due to repeated failed logins. Try again after "
                      f"{locked_until.strftime('%H:%M:%S')}.", "danger")
                return render_template("admin/login.html")

        if not admin or not check_password_hash(admin["password_hash"], password):
            if admin:
                attempts = admin["failed_attempts"] + 1
                locked_until = None
                if attempts >= MAX_ATTEMPTS:
                    locked_until = (datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
                    attempts = 0
                db.execute(
                    "UPDATE admin_users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                    (attempts, locked_until, admin["id"]),
                )
            flash("Invalid username or password.", "danger")
            return render_template("admin/login.html")

        if not admin["is_active"]:
            flash("This admin account is disabled.", "danger")
            return render_template("admin/login.html")

        db.execute(
            "UPDATE admin_users SET failed_attempts = 0, locked_until = NULL WHERE id = ?",
            (admin["id"],),
        )
        session.clear()
        session.permanent = True
        current_app.permanent_session_lifetime = timedelta(
            minutes=current_app.config["ADMIN_SESSION_TIMEOUT_MINUTES"]
        )
        session["admin_id"] = admin["id"]
        session["admin_username"] = admin["username"]
        write_audit_log(admin["username"], "LOGIN", "Auth", admin["id"])
        flash(f"Welcome, {admin['full_name'] or admin['username']}.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/login.html")


@bp.route("/admin/logout")
def admin_logout():
    username = session.get("admin_username")
    if username:
        write_audit_log(username, "LOGOUT", "Auth", session.get("admin_id"))
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("auth.admin_login"))