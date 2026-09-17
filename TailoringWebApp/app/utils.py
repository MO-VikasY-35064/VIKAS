import os
import re
import uuid
from datetime import datetime, date
from functools import wraps
from pathlib import Path

from flask import current_app, session, redirect, url_for, flash, request
from werkzeug.utils import secure_filename

from . import db

ORDER_STATUS_FLOW = [
    "ORDER_RECEIVED",
    "MEASUREMENT_CONFIRMED",
    "CUTTING",
    "STITCHING",
    "TRIAL_PENDING",
    "TRIAL_READY",
    "ALTERATION_REQUIRED",
    "FINAL_STITCHING",
    "READY_FOR_DELIVERY",
    "DELIVERED",
    "COMPLETED",
]
ORDER_STATUS_TERMINAL_EXTRA = ["CANCELLED", "ON_HOLD"]
ALL_ORDER_STATUSES = ORDER_STATUS_FLOW + ORDER_STATUS_TERMINAL_EXTRA

PAYMENT_STATUSES = ["PENDING", "SUCCESS", "FAILED", "VERIFIED", "REFUNDED"]

# BRS Section 11: configurable measurement fields, shared between the
# customer self-service form and the admin "take measurement" form.
MEASUREMENT_FIELDS = [
    ("blouse_length", "Blouse Length (in)"),
    ("shoulder", "Shoulder (in)"),
    ("bust", "Bust (in)"),
    ("waist", "Waist (in)"),
    ("armhole", "Armhole (in)"),
    ("sleeve_length", "Sleeve Length (in)"),
    ("sleeve_round", "Sleeve Round (in)"),
    ("neck_front", "Neck Front (in)"),
    ("neck_back", "Neck Back (in)"),
    ("neck_width", "Neck Width (in)"),
    ("neck_depth", "Neck Depth (in)"),
]


def save_new_measurement_version(customer_id, form, errors_out):
    """
    Validates form fields against MEASUREMENT_FIELDS and, if valid, inserts
    a new measurement version for the customer (never overwrites - BRS
    Section 11/29). Returns the new version number, or None if errors_out
    was populated. Used by both the customer self-service form and the
    admin "take measurement" form so the versioning logic lives in one place.
    """
    values = {}
    for field, label in MEASUREMENT_FIELDS:
        raw = (form.get(field) or "").strip()
        if raw == "":
            values[field] = None
            continue
        try:
            num = float(raw)
            if num <= 0 or num > 100:
                errors_out.append(f"{label} looks out of range.")
            values[field] = num
        except ValueError:
            errors_out.append(f"{label} must be a number.")
            values[field] = None

    other_notes = (form.get("other_notes") or "").strip()
    if errors_out:
        return None

    last = db.query(
        "SELECT MAX(version) v FROM measurements WHERE customer_id = ?",
        (customer_id,), one=True,
    )
    new_version = (last["v"] or 0) + 1
    db.execute("UPDATE measurements SET is_current = 0 WHERE customer_id = ?", (customer_id,))
    db.execute(
        """INSERT INTO measurements
           (customer_id, version, blouse_length, shoulder, bust, waist, armhole,
            sleeve_length, sleeve_round, neck_front, neck_back, neck_width, neck_depth,
            other_notes, is_current)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (customer_id, new_version, values["blouse_length"], values["shoulder"],
         values["bust"], values["waist"], values["armhole"], values["sleeve_length"],
         values["sleeve_round"], values["neck_front"], values["neck_back"],
         values["neck_width"], values["neck_depth"], other_notes or None),
    )
    return new_version


# ---------------------------------------------------------------------
# Auth decorators / session helpers  (BRS Section 6/8/35)
# ---------------------------------------------------------------------
def customer_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("customer_id"):
            flash("Please login to continue.", "warning")
            return redirect(url_for("auth.customer_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please login as admin to continue.", "warning")
            return redirect(url_for("auth.admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def current_customer():
    cid = session.get("customer_id")
    if not cid:
        return None
    return db.query("SELECT * FROM customers WHERE id = ?", (cid,), one=True)


def current_admin():
    aid = session.get("admin_id")
    if not aid:
        return None
    return db.query("SELECT * FROM admin_users WHERE id = ?", (aid,), one=True)


# ---------------------------------------------------------------------
# Validation  (BRS Section 34)
# ---------------------------------------------------------------------
def is_valid_mobile(mobile):
    return bool(re.fullmatch(r"[6-9]\d{9}", (mobile or "").strip()))


def is_valid_email(email):
    if not email:
        return True  # email is optional (BRS Section 6)
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))


def is_valid_password(password):
    return bool(password) and len(password) >= 6


# ---------------------------------------------------------------------
# Order numbers  (BRS Section 14: ORD202609110001, never reused)
# ---------------------------------------------------------------------
def generate_order_number():
    today_str = date.today().strftime("%Y%m%d")
    prefix = f"ORD{today_str}"
    row = db.query(
        "SELECT order_number FROM orders WHERE order_number LIKE ? ORDER BY id DESC",
        (f"{prefix}%",),
        one=True,
    )
    if row:
        last_seq = int(row["order_number"][-4:])
        seq = last_seq + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


# ---------------------------------------------------------------------
# Image storage  (BRS Section 3 / 20 / BR-017 / BR-018)
# ---------------------------------------------------------------------
def allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def save_image(file_storage, image_type, entity_id, uploaded_by="system"):
    """
    Saves an uploaded image under:
      uploads/Images/<IMAGE_TYPE>/<ENTITY_ID>/<TYPE>_<ENTITY>_<TIMESTAMP>_<UUID>.<ext>
    Never trusts the original filename (BR-017). Returns (file_name, file_path).
    """
    if not file_storage or file_storage.filename == "":
        raise ValueError("No file provided.")
    if not allowed_file(file_storage.filename):
        raise ValueError("Unsupported file type. Allowed: "
                          + ", ".join(current_app.config["ALLOWED_IMAGE_EXTENSIONS"]))

    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique = uuid.uuid4().hex[:6].upper()
    safe_entity = secure_filename(str(entity_id))
    new_filename = f"{image_type.upper()}_{safe_entity}_{timestamp}_{unique}.{ext}"

    folder = Path(current_app.config["UPLOAD_ROOT"]) / image_type / safe_entity
    folder.mkdir(parents=True, exist_ok=True)
    full_path = folder / new_filename
    file_storage.save(full_path)

    # Path stored in DB is relative to UPLOAD_ROOT so it survives moving
    # the server (BRS Section 31: avoid hard-coded paths).
    relative_path = f"{image_type}/{safe_entity}/{new_filename}"
    return new_filename, relative_path


# ---------------------------------------------------------------------
# Email  (BRS Section 21) - pluggable backend
# ---------------------------------------------------------------------
def _find_trial_image(order_number):
    """
    Trial images are saved by save_image() as:
      uploads/Images/Trial/<order_number>/TRIAL_<order_number>_<timestamp>_<uuid>.<ext>
    Multiple trial images can exist for one order (re-uploads); this
    returns the most recently modified one, or None if none exist.

    NOTE: confirm UPLOAD_ROOT points at ".../uploads/Images" - if it
    instead points at ".../uploads", change the line below to
    Path(current_app.config["UPLOAD_ROOT"]) / "Images" / "Trial" / order_number
    """
    folder = Path(current_app.config["UPLOAD_ROOT"]) / "Trial" / order_number
    if not folder.exists():
        return None
    matches = list(folder.glob(f"TRIAL_{order_number}_*.*"))
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


def send_trial_email(order, customer):
    """
    Queues the trial-ready email to send in a background thread, so the
    web request returns immediately instead of blocking on the full SMTP
    round-trip (connect + TLS + login + upload can take several seconds,
    more on a slow network). The actual outcome is written to email_logs
    once the send completes - check that table for this order/customer if
    you need to confirm delivery rather than relying on this return value.

    Returns (queued: bool, error_message) - queued is False only if we
    couldn't even attempt the send (e.g. no customer email on file).
    """
    if not customer["email"]:
        error_message = "Customer email not available."
        db.execute(
            """INSERT INTO email_logs (order_id, customer_id, email_to, email_type, status, error_message, sent_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (order["id"], customer["id"], customer["email"], "TRIAL_INVITE", "FAILED", error_message,
             datetime.now()),
        )
        return False, error_message

    import threading
    app = current_app._get_current_object()
    threading.Thread(
        target=_send_trial_email_background,
        args=(app, order, customer),
        daemon=True,
    ).start()
    return True, None


def _send_trial_email_background(app, order, customer):
    with app.app_context():
        backend = current_app.config["EMAIL_BACKEND"]
        subject = f"Your trial is ready - Order {order['order_number']}"
        body = (
            f"Dear {customer['name'] or 'Customer'},\n\n"
            f"Your blouse for order {order['order_number']} is ready for trial.\n"
            f"Please visit us at your convenience, or reply to this email to schedule a time.\n\n"
            f"Thank you,\nThe Tailoring Team"
        )
        image_path = _find_trial_image(order["order_number"])

        status, error_message = "SUCCESS", None
        try:
            if backend == "smtp":
                _send_via_smtp(customer["email"], subject, body, image_path=image_path)
            elif backend == "gmail_api":
                current_app.logger.info("[gmail_api] would send to %s: %s", customer["email"], subject)
            else:  # console / default - safe no-op for local/demo use
                current_app.logger.info(
                    "[EMAIL:console] To=%s Subject=%s Attachment=%s\n%s",
                    customer["email"], subject,
                    image_path if image_path else "none", body,
                )
        except Exception as exc:  # noqa: BLE001 - we want to log & record any failure
            current_app.logger.exception("Failed to send trial email")
            status, error_message = "FAILED", str(exc)

        db.execute(
            """INSERT INTO email_logs (order_id, customer_id, email_to, email_type, status, error_message, sent_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (order["id"], customer["id"], customer["email"], "TRIAL_INVITE", status, error_message,
             datetime.now()),
        )


def _prepare_email_image(image_path, max_dimension=1200, quality=70, max_bytes=400_000):
    """
    Returns (bytes, filename) for attaching image_path to an email, downscaled
    and re-compressed as JPEG so a large phone photo doesn't take forever to
    upload over a slow link. Falls back to the raw file if Pillow isn't
    available or the file is already small enough.
    """
    try:
        raw_size = image_path.stat().st_size
        if raw_size <= max_bytes:
            return image_path.read_bytes(), image_path.name

        from PIL import Image
        import io

        with Image.open(image_path) as im:
            im = im.convert("RGB")
            im.thumbnail((max_dimension, max_dimension))
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=quality, optimize=True)
            data = buf.getvalue()

        current_app.logger.info(
            "Compressed trial image %s: %d bytes -> %d bytes",
            image_path.name, raw_size, len(data),
        )
        return data, image_path.stem + ".jpg"
    except ImportError:
        current_app.logger.warning(
            "Pillow not installed; sending original image %s uncompressed (%d bytes)",
            image_path.name, image_path.stat().st_size,
        )
        return image_path.read_bytes(), image_path.name
    except Exception:
        current_app.logger.exception(
            "Failed to compress trial image %s; sending original", image_path.name
        )
        return image_path.read_bytes(), image_path.name


def _send_via_smtp(to_email, subject, body, image_path=None):
    import smtplib
    import socket
    import time
    from contextlib import contextmanager
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage

    @contextmanager
    def _force_ipv4_dns():
        """
        Some Windows setups (certain VPNs, some ISPs, virtual adapters) have
        IPv6 addresses configured in DNS but no actual working IPv6 route.
        Python's socket.getaddrinfo() asks for both address families by
        default, and on affected machines the whole dual-stack lookup can
        fail with [Errno 11001] getaddrinfo failed even though a plain
        nslookup/ping succeeds. Forcing IPv4-only resolution for the
        duration of the SMTP connection works around this without changing
        Windows network settings. The hostname itself is still used for the
        connection and TLS certificate check - only address resolution is
        restricted to IPv4.
        """
        original = socket.getaddrinfo

        def ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
            return original(host, port, socket.AF_INET, type, proto, flags)

        socket.getaddrinfo = ipv4_only
        try:
            yield
        finally:
            socket.getaddrinfo = original

    cfg = current_app.config
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = cfg["EMAIL_FROM"]
    msg["To"] = to_email
    msg.attach(MIMEText(body))

    if image_path and image_path.exists():
        img_bytes, img_filename = _prepare_email_image(image_path)
        img = MIMEImage(img_bytes)
        img.add_header("Content-Disposition", "attachment", filename=img_filename)
        msg.attach(img)
    elif image_path:
        current_app.logger.warning("Trial image not found at %s", image_path)

    current_app.logger.info(
        "SMTP connect attempt: host=%r port=%r (types: %s, %s)",
        cfg["SMTP_HOST"], cfg["SMTP_PORT"],
        type(cfg["SMTP_HOST"]).__name__, type(cfg["SMTP_PORT"]).__name__,
    )

    last_err = None
    for attempt in range(1, 4):
        try:
            with _force_ipv4_dns():
                with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=60) as server:
                    server.starttls()
                    server.login(cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"])
                    server.sendmail(cfg["EMAIL_FROM"], [to_email], msg.as_string())
            return
        except (socket.gaierror, TimeoutError, smtplib.SMTPServerDisconnected) as exc:
            last_err = exc
            current_app.logger.warning(
                "SMTP send failed (attempt %d/3): %s: %s",
                attempt, type(exc).__name__, exc,
            )
            if attempt < 3:
                time.sleep(2 * attempt)
    raise last_err


# ---------------------------------------------------------------------
# Configurable status-triggered emails
# ---------------------------------------------------------------------
def get_enabled_status_email_triggers():
    """
    Reads the admin-configured set of order statuses that should
    automatically email the customer, from website_settings
    (key 'email_trigger_statuses' - a comma-separated list of status
    codes, set via Admin > Settings). Returns a set of status codes.
    Empty/unset means no automatic status-change emails fire at all -
    admin opts in per status; skipping a status is just not selecting it.
    """
    row = db.query(
        "SELECT setting_value FROM website_settings WHERE setting_key = 'email_trigger_statuses'",
        one=True,
    )
    raw = (row["setting_value"] if row else "") or ""
    return {s.strip() for s in raw.split(",") if s.strip()}


_STATUS_EMAIL_SUBJECTS = {
    "ORDER_RECEIVED": "Your order has been received",
}


def send_status_email(order, customer, status):
    """
    Queues (in a background thread, same pattern as send_trial_email) a
    generic status-update email for order/status, but ONLY if that status
    is enabled in the admin-configured trigger list. Safe to call after
    every status change - it's a silent no-op if the status isn't
    configured to send an email, or if the customer has no email on file.
    Logged to email_logs the same way as the trial invite email.
    """
    if status not in get_enabled_status_email_triggers():
        return
    if not customer or not customer["email"]:
        return

    import threading
    app = current_app._get_current_object()
    threading.Thread(
        target=_send_status_email_background,
        args=(app, order, customer, status),
        daemon=True,
    ).start()


def _send_status_email_background(app, order, customer, status):
    with app.app_context():
        label = status.replace("_", " ").title()
        subject = _STATUS_EMAIL_SUBJECTS.get(status, f"Order {order['order_number']} update: {label}")
        if status == "ORDER_RECEIVED":
            body = (
                f"Dear {customer['name'] or 'Customer'},\n\n"
                f"Your order {order['order_number']} has been received. "
                f"We'll keep you updated as it progresses.\n\n"
                f"Thank you,\nThe Tailoring Team"
            )
        else:
            body = (
                f"Dear {customer['name'] or 'Customer'},\n\n"
                f"Your order {order['order_number']} status has been updated to: {label}.\n\n"
                f"Thank you,\nThe Tailoring Team"
            )

        backend = current_app.config["EMAIL_BACKEND"]
        db_status, error_message = "SUCCESS", None
        try:
            if backend == "smtp":
                _send_via_smtp(customer["email"], subject, body)
            elif backend == "gmail_api":
                current_app.logger.info("[gmail_api] would send to %s: %s", customer["email"], subject)
            else:  # console / default
                current_app.logger.info("[EMAIL:console] To=%s Subject=%s\n%s",
                                         customer["email"], subject, body)
        except Exception as exc:  # noqa: BLE001
            current_app.logger.exception("Failed to send status email")
            db_status, error_message = "FAILED", str(exc)

        db.execute(
            """INSERT INTO email_logs (order_id, customer_id, email_to, email_type, status, error_message, sent_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (order["id"], customer["id"], customer["email"], f"STATUS_{status}", db_status, error_message,
             datetime.now()),
        )



# ---------------------------------------------------------------------
# Audit log  (BRS Section 27 / BR-016)
# ---------------------------------------------------------------------
def write_audit_log(admin_username, action, module, record_id, old_value=None, new_value=None):
    db.execute(
        """INSERT INTO audit_logs (admin_user, action, module, record_id, old_value, new_value, ip_address)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (admin_username, action, module, str(record_id), old_value, new_value,
         request.remote_addr if request else None),
    )


# ---------------------------------------------------------------------
# Misc formatting helpers (used in templates)
# ---------------------------------------------------------------------
def inr(amount):
    try:
        return f"\u20b9{float(amount):,.2f}"
    except (TypeError, ValueError):
        return amount
