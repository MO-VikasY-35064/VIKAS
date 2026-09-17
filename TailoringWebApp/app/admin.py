import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash

from . import db
from .utils import (
    admin_login_required, current_admin, save_image, send_trial_email,
    write_audit_log, ALL_ORDER_STATUSES, PAYMENT_STATUSES,
    MEASUREMENT_FIELDS, save_new_measurement_version,
    is_valid_mobile, is_valid_email, send_status_email,
)

bp = Blueprint("admin", __name__)


# =====================================================================
# Dashboard  (BRS Section 9)
# =====================================================================
@bp.route("/")
@bp.route("/dashboard")
@admin_login_required
def dashboard():
    def count(sql, params=()):
        return db.query(sql, params, one=True)["c"]

    kpis = {
        "total_customers": count("SELECT COUNT(*) c FROM customers"),
        "total_orders": count("SELECT COUNT(*) c FROM orders"),
        "new_orders": count("SELECT COUNT(*) c FROM orders WHERE status = 'ORDER_RECEIVED'"),
        "in_cutting": count("SELECT COUNT(*) c FROM orders WHERE status = 'CUTTING'"),
        "in_stitching": count("SELECT COUNT(*) c FROM orders WHERE status IN ('STITCHING','FINAL_STITCHING')"),
        "in_trial": count("SELECT COUNT(*) c FROM orders WHERE status IN ('TRIAL_PENDING','TRIAL_READY','ALTERATION_REQUIRED')"),
        "ready_for_delivery": count("SELECT COUNT(*) c FROM orders WHERE status = 'READY_FOR_DELIVERY'"),
        "completed": count("SELECT COUNT(*) c FROM orders WHERE status = 'COMPLETED'"),
        "cancelled": count("SELECT COUNT(*) c FROM orders WHERE status = 'CANCELLED'"),
    }
    totals = db.query(
        "SELECT COALESCE(SUM(total_amount),0) t, COALESCE(SUM(amount_received),0) r, "
        "COALESCE(SUM(amount_pending),0) p FROM orders WHERE status != 'CANCELLED'",
        one=True,
    )
    kpis["total_amount"] = totals["t"]
    kpis["amount_received"] = totals["r"]
    kpis["amount_pending"] = totals["p"]

    today = date.today().isoformat()
    todays_deliveries = db.query(
        """SELECT o.order_number, c.name, c.mobile, o.status FROM orders o
           JOIN customers c ON c.id = o.customer_id
           WHERE o.delivery_date = ? AND o.status != 'CANCELLED'""",
        (today,),
    )
    upcoming = db.query(
        """SELECT o.order_number, c.name, c.mobile, o.delivery_date, o.status FROM orders o
           JOIN customers c ON c.id = o.customer_id
           WHERE o.delivery_date > ? AND o.status NOT IN ('CANCELLED','COMPLETED','DELIVERED')
           ORDER BY o.delivery_date""",
        (today,),
    )[:10]
    return render_template("admin/dashboard.html", kpis=kpis, todays_deliveries=todays_deliveries,
                            upcoming=upcoming)


# =====================================================================
# Customers  (BRS Section 10)
# =====================================================================
@bp.route("/customers")
@admin_login_required
def customers():
    q = request.args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        rows = db.query(
            """SELECT * FROM customers
               WHERE mobile LIKE ? OR name LIKE ? OR email LIKE ?
               ORDER BY created_at DESC""",
            (like, like, like),
        )
    else:
        rows = db.query("SELECT * FROM customers ORDER BY created_at DESC")
    return render_template("admin/customers.html", customers=rows, q=q)


@bp.route("/customers/new", methods=["GET", "POST"])
@admin_login_required
def new_customer():
    """
    Admin-side customer creation (BRS Section 10: 'Add Customer'), for
    walk-in customers or those registered over the phone rather than
    through self-service signup. Mobile is still mandatory & unique
    (BR-001/BR-002); a temporary password is generated so the customer
    can log in online later if they want to (e.g. to track their order).
    """
    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()

        errors = []
        if not is_valid_mobile(mobile):
            errors.append("Enter a valid 10-digit mobile number.")
        if not is_valid_email(email):
            errors.append("Enter a valid email address.")
        existing = db.query("SELECT id FROM customers WHERE mobile = ?", (mobile,), one=True)
        if existing:
            errors.append("A customer with this mobile number already exists.")  # BR-002

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/customer_form.html", form=request.form)

        temp_password = uuid.uuid4().hex[:8]
        customer_id = db.execute(
            "INSERT INTO customers (mobile, password_hash, name, email, address) VALUES (?, ?, ?, ?, ?)",
            (mobile, generate_password_hash(temp_password), name or None, email or None, address or None),
        )
        write_audit_log(session["admin_username"], "CREATE", "Customer", customer_id, None, mobile)
        flash(f"Customer added. Temporary login password: {temp_password} "
              f"(share this with the customer if they want to log in online - "
              f"they can also just be helped in person going forward).", "success")
        return redirect(url_for("admin.customer_detail", customer_id=customer_id))

    return render_template("admin/customer_form.html", form={})


@bp.route("/customers/<int:customer_id>")
@admin_login_required
def customer_detail(customer_id):
    customer = db.query("SELECT * FROM customers WHERE id = ?", (customer_id,), one=True)
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for("admin.customers"))
    orders = db.query(
        """SELECT o.*, d.name as design_name FROM orders o JOIN designs d ON d.id = o.design_id
           WHERE o.customer_id = ? ORDER BY o.created_at DESC""",
        (customer_id,),
    )
    measurements = db.query(
        "SELECT * FROM measurements WHERE customer_id = ? ORDER BY version DESC", (customer_id,)
    )
    return render_template("admin/customer_detail.html", customer=customer, orders=orders,
                            measurements=measurements)


@bp.route("/customers/<int:customer_id>/toggle-active", methods=["POST"])
@admin_login_required
def toggle_customer_active(customer_id):
    customer = db.query("SELECT * FROM customers WHERE id = ?", (customer_id,), one=True)
    if customer:
        new_val = 0 if customer["is_active"] else 1
        db.execute("UPDATE customers SET is_active = ? WHERE id = ?", (new_val, customer_id))
        write_audit_log(session["admin_username"], "TOGGLE_ACTIVE", "Customer", customer_id,
                         str(customer["is_active"]), str(new_val))
        flash("Customer status updated.", "success")
    return redirect(url_for("admin.customer_detail", customer_id=customer_id))


# =====================================================================
# Measurements  (BRS Section 11 - admin can create/maintain measurements,
# e.g. when a customer visits the shop in person and admin takes them)
# =====================================================================
@bp.route("/measurements/new", methods=["GET", "POST"])
@admin_login_required
def quick_measurement():
    """
    One-step 'walk-in' flow: admin enters the customer's mobile (+ name/
    email if new) AND the measurement values together. If a customer with
    that mobile already exists, the measurement is added to their record;
    if not, the customer is created first (BRS Section 10 'Add Customer')
    and then the measurement is saved against them - no separate trip to
    "Add Customer" required first.
    """
    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()

        errors = []
        if not is_valid_mobile(mobile):
            errors.append("Enter a valid 10-digit mobile number.")
        if not is_valid_email(email):
            errors.append("Enter a valid email address.")

        customer = db.query("SELECT * FROM customers WHERE mobile = ?", (mobile,), one=True)
        is_new_customer = customer is None

        if not errors:
            if customer is None:
                temp_password = uuid.uuid4().hex[:8]
                customer_id = db.execute(
                    "INSERT INTO customers (mobile, password_hash, name, email) VALUES (?, ?, ?, ?)",
                    (mobile, generate_password_hash(temp_password), name or None, email or None),
                )
                write_audit_log(session["admin_username"], "CREATE", "Customer", customer_id, None, mobile)
            else:
                customer_id = customer["id"]

            measurement_errors = []
            new_version = save_new_measurement_version(customer_id, request.form, measurement_errors)

            if measurement_errors:
                # Roll back the just-created customer if the measurement itself
                # was invalid, so a failed submit doesn't leave an empty record.
                if is_new_customer:
                    db.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
                errors.extend(measurement_errors)
            else:
                write_audit_log(session["admin_username"], "CREATE", "Measurement", customer_id,
                                 None, f"version {new_version}")
                if is_new_customer:
                    flash(f"New customer added and measurement saved (version {new_version}).", "success")
                else:
                    flash(f"Measurement saved for {customer['name'] or customer['mobile']} "
                          f"(version {new_version}).", "success")
                return redirect(url_for("admin.customer_detail", customer_id=customer_id))

        for e in errors:
            flash(e, "danger")
        return render_template("admin/quick_measurement_form.html",
                                fields=MEASUREMENT_FIELDS, form=request.form)

    return render_template("admin/quick_measurement_form.html",
                            fields=MEASUREMENT_FIELDS, form={})


@bp.route("/customers/<int:customer_id>/measurements/new", methods=["GET", "POST"])
@admin_login_required
def new_measurement(customer_id):
    customer = db.query("SELECT * FROM customers WHERE id = ?", (customer_id,), one=True)
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for("admin.customers"))

    current = db.query(
        "SELECT * FROM measurements WHERE customer_id = ? AND is_current = 1",
        (customer_id,), one=True,
    )

    if request.method == "POST":
        errors = []
        new_version = save_new_measurement_version(customer_id, request.form, errors)
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/measurement_form.html", customer=customer,
                                    fields=MEASUREMENT_FIELDS, form_values=request.form)

        write_audit_log(session["admin_username"], "CREATE", "Measurement", customer_id,
                         None, f"version {new_version}")
        flash(f"Measurement saved for {customer['name'] or customer['mobile']} (version {new_version}).",
              "success")
        return redirect(url_for("admin.customer_detail", customer_id=customer_id))

    return render_template("admin/measurement_form.html", customer=customer,
                            fields=MEASUREMENT_FIELDS,
                            form_values=dict(current) if current else {})


@bp.route("/customers/<int:customer_id>/measurements/<int:measurement_id>")
@admin_login_required
def measurement_detail(customer_id, measurement_id):
    customer = db.query("SELECT * FROM customers WHERE id = ?", (customer_id,), one=True)
    measurement = db.query(
        "SELECT * FROM measurements WHERE id = ? AND customer_id = ?",
        (measurement_id, customer_id), one=True,
    )
    if not customer or not measurement:
        flash("Measurement record not found.", "danger")
        return redirect(url_for("admin.customers"))

    # Orders that were placed using this specific measurement snapshot
    # (BRS Section 29: orders keep the version used at the time, unaffected
    # by later updates - shown here for traceability).
    orders_using_this = db.query(
        """SELECT o.order_number, o.status, d.name as design_name FROM orders o
           JOIN designs d ON d.id = o.design_id
           WHERE o.measurement_id = ?""",
        (measurement_id,),
    )
    return render_template("admin/measurement_detail.html", customer=customer,
                            measurement=measurement, fields=MEASUREMENT_FIELDS,
                            orders_using_this=orders_using_this)


# =====================================================================
# Designs  (BRS Section 12)
# =====================================================================
@bp.route("/designs")
@admin_login_required
def designs():
    rows = db.query("SELECT * FROM designs ORDER BY created_at DESC")
    return render_template("admin/designs.html", designs=rows)


@bp.route("/designs/new", methods=["GET", "POST"])
@admin_login_required
def new_design():
    if request.method == "POST":
        data, image_path = _read_design_form(), None
        design_id = db.execute(
            """INSERT INTO designs (name, description, category, neck_style, sleeve_style,
               blouse_length, customisation_details, base_price, additional_charges, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data["name"], data["description"], data["category"], data["neck_style"],
             data["sleeve_style"], data["blouse_length"], data["customisation_details"],
             data["base_price"], data["additional_charges"], data["status"]),
        )
        file = request.files.get("image")
        if file and file.filename:
            try:
                _, image_path = save_image(file, "BlouseDesign", design_id, session["admin_username"])
                db.execute("UPDATE designs SET image_path = ? WHERE id = ?", (image_path, design_id))
            except ValueError as e:
                flash(f"Design saved, but image upload failed: {e}", "warning")
        write_audit_log(session["admin_username"], "CREATE", "Design", design_id, None, data["name"])
        flash("Design created.", "success")
        return redirect(url_for("admin.designs"))
    return render_template("admin/design_form.html", design=None)


@bp.route("/designs/<int:design_id>/edit", methods=["GET", "POST"])
@admin_login_required
def edit_design(design_id):
    design = db.query("SELECT * FROM designs WHERE id = ?", (design_id,), one=True)
    if not design:
        flash("Design not found.", "danger")
        return redirect(url_for("admin.designs"))

    if request.method == "POST":
        data = _read_design_form()
        db.execute(
            """UPDATE designs SET name=?, description=?, category=?, neck_style=?, sleeve_style=?,
               blouse_length=?, customisation_details=?, base_price=?, additional_charges=?, status=?,
               modified_at = ? WHERE id = ?""",
            (data["name"], data["description"], data["category"], data["neck_style"],
             data["sleeve_style"], data["blouse_length"], data["customisation_details"],
             data["base_price"], data["additional_charges"], data["status"],
             datetime.utcnow(), design_id),
        )
        file = request.files.get("image")
        if file and file.filename:
            try:
                _, image_path = save_image(file, "BlouseDesign", design_id, session["admin_username"])
                db.execute("UPDATE designs SET image_path = ? WHERE id = ?", (image_path, design_id))
            except ValueError as e:
                flash(f"Design updated, but image upload failed: {e}", "warning")
        write_audit_log(session["admin_username"], "UPDATE", "Design", design_id,
                         design["name"], data["name"])
        flash("Design updated. (Note: existing orders keep their original price - BR-013)", "success")
        return redirect(url_for("admin.designs"))

    return render_template("admin/design_form.html", design=design)


def _read_design_form():
    def f(key, cast=str, default=""):
        val = request.form.get(key, default)
        return cast(val) if val != "" else (0 if cast in (int, float) else None)
    return {
        "name": request.form.get("name", "").strip(),
        "description": request.form.get("description", "").strip(),
        "category": request.form.get("category", "").strip(),
        "neck_style": request.form.get("neck_style", "").strip(),
        "sleeve_style": request.form.get("sleeve_style", "").strip(),
        "blouse_length": request.form.get("blouse_length", "").strip(),
        "customisation_details": request.form.get("customisation_details", "").strip(),
        "base_price": f("base_price", float, "0"),
        "additional_charges": f("additional_charges", float, "0"),
        "status": request.form.get("status", "ACTIVE"),
    }


# =====================================================================
# Gallery  (BRS Section 13)
# =====================================================================
@bp.route("/gallery", methods=["GET", "POST"])
@admin_login_required
def gallery():
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        display_order = int(request.form.get("display_order") or 0)
        file = request.files.get("image")
        try:
            # Save the image FIRST. No gallery row is created unless this
            # succeeds, so a failed/missing upload never leaves a broken
            # row behind with an empty image_path (that was the original bug).
            # There's no gallery_id yet at this point, so a short UUID is
            # used as the folder/filename key instead - save_image only
            # uses it for naming on disk, it isn't a DB foreign key.
            temp_key = uuid.uuid4().hex[:8]
            file_name, image_path = save_image(file, "Gallery", temp_key, session["admin_username"])

            gallery_id = db.execute(
                "INSERT INTO gallery (image_path, category, description, display_order) VALUES (?, ?, ?, ?)",
                (image_path, category, description, display_order),
            )
            write_audit_log(session["admin_username"], "CREATE", "Gallery", gallery_id, None, category)
            flash("Gallery image added.", "success")
        except ValueError as e:
            flash(str(e), "danger")
        return redirect(url_for("admin.gallery"))

    rows = db.query("SELECT * FROM gallery ORDER BY display_order")
    return render_template("admin/gallery.html", gallery=rows)


@bp.route("/gallery/<int:gallery_id>/toggle", methods=["POST"])
@admin_login_required
def toggle_gallery(gallery_id):
    row = db.query("SELECT * FROM gallery WHERE id = ?", (gallery_id,), one=True)
    if row:
        db.execute("UPDATE gallery SET is_active = ? WHERE id = ?",
                   (0 if row["is_active"] else 1, gallery_id))
    return redirect(url_for("admin.gallery"))


# =====================================================================
# Orders  (BRS Section 17/18/19/20/21/25)
# =====================================================================
@bp.route("/orders")
@admin_login_required
def orders():
    status = request.args.get("status", "").strip()
    q = request.args.get("q", "").strip()
    sql = """SELECT o.*, c.name as customer_name, c.mobile, d.name as design_name
              FROM orders o JOIN customers c ON c.id = o.customer_id
              JOIN designs d ON d.id = o.design_id WHERE 1=1"""
    params = []
    if status:
        sql += " AND o.status = ?"
        params.append(status)
    if q:
        sql += " AND (o.order_number LIKE ? OR c.mobile LIKE ? OR c.name LIKE ?)"
        like = f"%{q}%"
        params += [like, like, like]
    sql += " ORDER BY o.created_at DESC"
    rows = db.query(sql, params)
    return render_template("admin/orders.html", orders=rows, statuses=ALL_ORDER_STATUSES,
                            selected_status=status, q=q)


@bp.route("/orders/<order_number>")
@admin_login_required
def order_detail(order_number):
    order = db.query(
        """SELECT o.*, c.name as customer_name, c.mobile, c.email, d.name as design_name
           FROM orders o JOIN customers c ON c.id = o.customer_id
           JOIN designs d ON d.id = o.design_id WHERE o.order_number = ?""",
        (order_number,), one=True,
    )
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("admin.orders"))

    history = db.query(
        "SELECT * FROM order_status_history WHERE order_id = ? ORDER BY created_at",
        (order["id"],),
    )
    trial_images = db.query(
        "SELECT * FROM order_images WHERE order_id = ? AND image_type='Trial' AND is_active=1 "
        "ORDER BY uploaded_at DESC",
        (order["id"],),
    )
    reference_images = db.query(
        "SELECT * FROM order_images WHERE order_id = ? AND image_type='CustomerReference' AND is_active=1",
        (order["id"],),
    )
    payments = db.query("SELECT * FROM payments WHERE order_id = ? ORDER BY created_at", (order["id"],))
    emails = db.query("SELECT * FROM email_logs WHERE order_id = ? ORDER BY sent_at DESC", (order["id"],))
    measurement = db.query("SELECT * FROM measurements WHERE id = ?", (order["measurement_id"],), one=True)

    return render_template(
        "admin/order_detail.html", order=order, history=history, trial_images=trial_images,
        reference_images=reference_images, payments=payments, emails=emails,
        measurement=measurement, statuses=ALL_ORDER_STATUSES, payment_statuses=PAYMENT_STATUSES,
    )


@bp.route("/orders/<order_number>/status", methods=["POST"])
@admin_login_required
def update_status(order_number):
    order = db.query("SELECT * FROM orders WHERE order_number = ?", (order_number,), one=True)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("admin.orders"))

    new_status = request.form.get("status")
    remarks = request.form.get("remarks", "").strip()
    if new_status not in ALL_ORDER_STATUSES:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin.order_detail", order_number=order_number))

    db.execute("UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
               (new_status, datetime.utcnow(), order["id"]))
    db.execute(
        """INSERT INTO order_status_history (order_id, previous_status, new_status, remarks, updated_by)
           VALUES (?, ?, ?, ?, ?)""",
        (order["id"], order["status"], new_status, remarks or None, session["admin_username"]),
    )
    write_audit_log(session["admin_username"], "STATUS_CHANGE", "Order", order["id"],
                     order["status"], new_status)  # BR-010 / BR-016

    # Automatic status-change email - only fires if new_status is one of
    # the statuses the admin has enabled in Settings > Email Triggers.
    # Skipping a status is simply not selecting it there; no code change
    # needed to add/remove a status from the trigger list.
    customer = db.query("SELECT * FROM customers WHERE id = ?", (order["customer_id"],), one=True)
    send_status_email(order, customer, new_status)

    flash(f"Order status updated to {new_status.replace('_', ' ').title()}.", "success")
    return redirect(url_for("admin.order_detail", order_number=order_number))


@bp.route("/orders/<order_number>/payment", methods=["POST"])
@admin_login_required
def add_payment(order_number):
    order = db.query("SELECT * FROM orders WHERE order_number = ?", (order_number,), one=True)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("admin.orders"))

    try:
        amount = float(request.form.get("amount", "0"))
    except ValueError:
        amount = 0

    mode = request.form.get("mode", "CASH")
    reference_no = request.form.get("reference_no", "").strip() or None
    status = request.form.get("status", "SUCCESS")

    # amount_pending/amount_received/total_amount come back as
    # decimal.Decimal from pyodbc/MSSQL but as float from SQLite - cast
    # explicitly wherever they're used in arithmetic so this works on both.
    amount_pending = float(order["amount_pending"])

    errors = []
    if amount <= 0:
        errors.append("Payment amount must be greater than zero.")
    if amount > amount_pending + 0.01:
        errors.append(f"Payment amount cannot exceed the pending amount "
                       f"({amount_pending:.2f}).")  # BR-009
    if reference_no:
        dup = db.query(
            "SELECT id FROM payments WHERE order_id = ? AND reference_no = ?",
            (order["id"], reference_no), one=True,
        )
        if dup:
            errors.append("This payment reference has already been recorded for this order.")

    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("admin.order_detail", order_number=order_number))

    db.execute(
        """INSERT INTO payments (order_id, amount, mode, reference_no, status, verified_by)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (order["id"], amount, mode, reference_no, status, session["admin_username"]),
    )

    if status in ("SUCCESS", "VERIFIED"):
        new_received = float(order["amount_received"]) + amount
        new_pending = max(float(order["total_amount"]) - new_received, 0)  # BR-008, never negative
        db.execute(
            "UPDATE orders SET amount_received = ?, amount_pending = ?, payment_status = ? WHERE id = ?",
            (new_received, new_pending, status, order["id"]),
        )
    write_audit_log(session["admin_username"], "PAYMENT_RECORDED", "Order", order["id"],
                     None, f"{amount} via {mode}")
    flash("Payment recorded.", "success")
    return redirect(url_for("admin.order_detail", order_number=order_number))


@bp.route("/orders/<order_number>/trial-image", methods=["POST"])
@admin_login_required
def upload_trial_image(order_number):
    order = db.query("SELECT * FROM orders WHERE order_number = ?", (order_number,), one=True)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("admin.orders"))

    file = request.files.get("image")
    try:
        file_name, file_path = save_image(file, "Trial", order["order_number"], session["admin_username"])
        db.execute(
            """INSERT INTO order_images (order_id, customer_id, image_type, file_name, file_path, uploaded_by)
               VALUES (?, ?, 'Trial', ?, ?, ?)""",
            (order["id"], order["customer_id"], file_name, file_path, session["admin_username"]),
        )
        # BR-011: trial image existing enables the "Send Trial Message" action
        if order["status"] in ("TRIAL_PENDING",):
            db.execute("UPDATE orders SET status = 'TRIAL_READY', updated_at = ? WHERE id = ?",
                       (datetime.utcnow(), order["id"]))
            db.execute(
                """INSERT INTO order_status_history (order_id, previous_status, new_status, remarks, updated_by)
                   VALUES (?, ?, 'TRIAL_READY', 'Trial image uploaded', ?)""",
                (order["id"], order["status"], session["admin_username"]),
            )
        write_audit_log(session["admin_username"], "TRIAL_IMAGE_UPLOAD", "Order", order["id"])
        flash("Trial image uploaded. You can now send the trial notification.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.order_detail", order_number=order_number))


@bp.route("/orders/<order_number>/trial-image/<int:image_id>/delete", methods=["POST"])
@admin_login_required
def delete_trial_image(order_number, image_id):
    """
    Removes a trial image both from disk and from the order_images table
    (soft delete via is_active=0, consistent with how gallery/customers
    handle deactivation elsewhere in this app - keeps the DB row for audit
    history while the physical file is actually removed from the folder).
    """
    order = db.query("SELECT * FROM orders WHERE order_number = ?", (order_number,), one=True)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("admin.orders"))

    image = db.query(
        "SELECT * FROM order_images WHERE id = ? AND order_id = ? AND image_type = 'Trial'",
        (image_id, order["id"]), one=True,
    )
    if not image:
        flash("Trial image not found.", "danger")
        return redirect(url_for("admin.order_detail", order_number=order_number))

    full_path = Path(current_app.config["UPLOAD_ROOT"]) / image["file_path"]
    try:
        full_path.unlink(missing_ok=True)
    except OSError as e:
        current_app.logger.warning("Could not delete trial image file %s: %s", full_path, e)
        flash("Image removed from the order, but the file could not be deleted from disk.", "warning")
    else:
        flash("Trial image removed.", "success")

    db.execute("UPDATE order_images SET is_active = 0 WHERE id = ?", (image_id,))
    write_audit_log(session["admin_username"], "TRIAL_IMAGE_DELETE", "Order", order["id"],
                     image["file_path"], None)
    return redirect(url_for("admin.order_detail", order_number=order_number))


@bp.route("/orders/<order_number>/send-trial-email", methods=["POST"])
@admin_login_required
def send_trial_notification(order_number):
    order = db.query("SELECT * FROM orders WHERE order_number = ?", (order_number,), one=True)
    customer = db.query("SELECT * FROM customers WHERE id = ?", (order["customer_id"],), one=True)

    has_trial_image = db.query(
        "SELECT id FROM order_images WHERE order_id = ? AND image_type='Trial' AND is_active=1",
        (order["id"],), one=True,
    )
    if not has_trial_image:
        flash("Cannot send trial message: no trial image has been uploaded yet.", "danger")  # BR-011
        return redirect(url_for("admin.order_detail", order_number=order_number))

    if not customer["email"]:
        flash("Email not available for this customer. Please contact them manually.", "warning")
        return redirect(url_for("admin.order_detail", order_number=order_number))

    success, error = send_trial_email(order, customer)
    write_audit_log(session["admin_username"], "SEND_TRIAL_EMAIL", "Order", order["id"],
                     None, "SUCCESS" if success else f"FAILED: {error}")
    flash("Trial email sent." if success else f"Failed to send trial email: {error}",
          "success" if success else "danger")
    return redirect(url_for("admin.order_detail", order_number=order_number))


@bp.route("/orders/<order_number>/cancel", methods=["POST"])
@admin_login_required
def cancel_order(order_number):
    order = db.query("SELECT * FROM orders WHERE order_number = ?", (order_number,), one=True)
    reason = request.form.get("reason", "").strip()
    if order and order["status"] not in ("DELIVERED", "COMPLETED", "CANCELLED"):
        db.execute(
            "UPDATE orders SET status='CANCELLED', cancellation_reason=?, updated_at=? WHERE id=?",
            (reason or None, datetime.utcnow(), order["id"]),
        )
        db.execute(
            """INSERT INTO order_status_history (order_id, previous_status, new_status, remarks, updated_by)
               VALUES (?, ?, 'CANCELLED', ?, ?)""",
            (order["id"], order["status"], reason or "Cancelled by admin", session["admin_username"]),
        )
        write_audit_log(session["admin_username"], "CANCEL", "Order", order["id"], order["status"], "CANCELLED")
        flash("Order cancelled.", "info")
    return redirect(url_for("admin.order_detail", order_number=order_number))


@bp.route("/orders/<order_number>/delete", methods=["POST"])
@admin_login_required
def delete_order(order_number):
    """
    Permanently deletes an order and everything tied to it: trial/reference
    image files on disk, and the order_images, order_status_history,
    payments, and email_logs rows referencing it (deleted first so this
    works even on the MSSQL schema, which has foreign keys back to orders).
    This is a hard delete, not a status change - there is no undo.
    """
    order = db.query("SELECT * FROM orders WHERE order_number = ?", (order_number,), one=True)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("admin.orders"))

    images = db.query("SELECT * FROM order_images WHERE order_id = ?", (order["id"],))
    for image in images:
        full_path = Path(current_app.config["UPLOAD_ROOT"]) / image["file_path"]
        try:
            full_path.unlink(missing_ok=True)
        except OSError as e:
            current_app.logger.warning("Could not delete order image file %s: %s", full_path, e)

    db.execute("DELETE FROM order_images WHERE order_id = ?", (order["id"],))
    db.execute("DELETE FROM order_status_history WHERE order_id = ?", (order["id"],))
    db.execute("DELETE FROM payments WHERE order_id = ?", (order["id"],))
    db.execute("DELETE FROM email_logs WHERE order_id = ?", (order["id"],))
    db.execute("DELETE FROM orders WHERE id = ?", (order["id"],))

    write_audit_log(session["admin_username"], "DELETE", "Order", order["id"],
                     order_number, None)
    flash(f"Order {order_number} deleted.", "info")
    return redirect(url_for("admin.orders"))


@bp.route("/orders/<order_number>/delivery-date", methods=["POST"])
@admin_login_required
def update_delivery_date(order_number):
    order = db.query("SELECT * FROM orders WHERE order_number = ?", (order_number,), one=True)
    new_date = request.form.get("delivery_date", "").strip()
    if order and new_date:
        try:
            parsed = datetime.strptime(new_date, "%Y-%m-%d").date()
            db.execute("UPDATE orders SET delivery_date = ?, updated_at = ? WHERE id = ?",
                       (parsed.isoformat(), datetime.utcnow(), order["id"]))
            write_audit_log(session["admin_username"], "DELIVERY_DATE_CHANGE", "Order", order["id"],
                             order["delivery_date"], parsed.isoformat())
            flash("Delivery date updated.", "success")
        except ValueError:
            flash("Invalid date.", "danger")
    return redirect(url_for("admin.order_detail", order_number=order_number))


# =====================================================================
# Reports  (BRS Section 36.8)
# =====================================================================
@bp.route("/reports")
@admin_login_required
def reports():
    by_status = db.query("SELECT status, COUNT(*) c FROM orders GROUP BY status")
    by_design = db.query(
        """SELECT d.name, COUNT(o.id) c, CAST(COALESCE(SUM(o.total_amount),0) AS FLOAT) revenue
           FROM designs d LEFT JOIN orders o ON o.design_id = d.id
           GROUP BY d.id, d.name ORDER BY c DESC"""
    )
    # Grouped in Python rather than SQL: SQLite's date()/LIMIT and SQL
    # Server's TOP/CONVERT are different enough that doing this in the
    # database would mean two separate queries per engine. Order volume
    # is low enough for a tailoring shop that this is negligible either way.
    raw_orders = db.query(
        "SELECT created_at, total_amount FROM orders WHERE status != 'CANCELLED'"
    )
    daily_totals = {}
    for o in raw_orders:
        day = str(o["created_at"])[:10]
        bucket = daily_totals.setdefault(day, {"revenue": 0.0, "orders": 0})
        # total_amount comes back as decimal.Decimal from pyodbc/MSSQL but
        # as float from SQLite - cast explicitly so this works on both.
        bucket["revenue"] += float(o["total_amount"] or 0)
        bucket["orders"] += 1
    daily_revenue = [
        {"day": day, "revenue": v["revenue"], "orders": v["orders"]}
        for day, v in sorted(daily_totals.items(), reverse=True)
    ][:14]

    pending_payments = db.query(
        """SELECT o.order_number, c.name, c.mobile, o.amount_pending FROM orders o
           JOIN customers c ON c.id = o.customer_id
           WHERE o.amount_pending > 0 AND o.status != 'CANCELLED'
           ORDER BY o.amount_pending DESC"""
    )
    return render_template("admin/reports.html", by_status=by_status, by_design=by_design,
                            daily_revenue=daily_revenue, pending_payments=pending_payments)


# =====================================================================
# Settings  (BRS Section 26)
# =====================================================================
@bp.route("/settings", methods=["GET", "POST"])
@admin_login_required
def settings():
    if request.method == "POST":
        for key in ("brand_name", "about_us", "address", "contact_number", "contact_email"):
            value = request.form.get(key, "").strip()
            db.upsert_setting(key, value)

        # Brand logo (BR: admin-uploaded, shown on the public home page).
        # Fixed entity key "brand" since there's only ever one logo - not
        # tied to a design/gallery/order id like other image uploads.
        logo_file = request.files.get("logo")
        if logo_file and logo_file.filename:
            try:
                _, logo_path = save_image(logo_file, "Logo", "brand", session["admin_username"])
                db.upsert_setting("logo_path", logo_path)
            except ValueError as e:
                flash(f"Other settings saved, but logo upload failed: {e}", "warning")

        # Email trigger configuration: which order statuses automatically
        # send the customer a notification email. Skipping a status is
        # just not checking its box - no separate "skip list" needed.
        selected_statuses = request.form.getlist("email_trigger_statuses")
        valid_selected = [s for s in selected_statuses if s in ALL_ORDER_STATUSES]
        db.upsert_setting("email_trigger_statuses", ",".join(valid_selected))

        write_audit_log(session["admin_username"], "UPDATE", "WebsiteSettings", "settings")
        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings"))

    rows = db.query("SELECT setting_key, setting_value FROM website_settings")
    settings_map = {r["setting_key"]: r["setting_value"] for r in rows}
    enabled_statuses = {
        s.strip() for s in (settings_map.get("email_trigger_statuses") or "").split(",") if s.strip()
    }
    return render_template("admin/settings.html", settings=settings_map,
                            all_statuses=ALL_ORDER_STATUSES, enabled_statuses=enabled_statuses)


# =====================================================================
# Audit log  (BRS Section 27)
# =====================================================================
@bp.route("/audit-logs")
@admin_login_required
def audit_logs():
    rows = db.query("SELECT * FROM audit_logs ORDER BY created_at DESC")[:200]
    return render_template("admin/audit_logs.html", logs=rows)
