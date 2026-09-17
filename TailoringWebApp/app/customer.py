from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

from . import db
from .utils import (
    customer_login_required, current_customer, generate_order_number,
    save_image, PAYMENT_STATUSES, MEASUREMENT_FIELDS, save_new_measurement_version,
    send_status_email,
)

bp = Blueprint("customer", __name__)


@bp.route("/dashboard")
@customer_login_required
def dashboard():
    customer = current_customer()
    orders = db.query(
        """SELECT o.*, d.name as design_name FROM orders o
           JOIN designs d ON d.id = o.design_id
           WHERE o.customer_id = ? ORDER BY o.created_at DESC""",
        (customer["id"],),
    )[:5]
    measurement = db.query(
        "SELECT * FROM measurements WHERE customer_id = ? AND is_current = 1",
        (customer["id"],), one=True,
    )
    return render_template("customer/dashboard.html", customer=customer, orders=orders,
                            measurement=measurement)


@bp.route("/profile", methods=["GET", "POST"])
@customer_login_required
def profile():
    customer = current_customer()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        db.execute(
            "UPDATE customers SET name = ?, email = ?, address = ? WHERE id = ?",
            (name or None, email or None, address or None, customer["id"]),
        )
        flash("Profile updated.", "success")
        return redirect(url_for("customer.profile"))
    return render_template("customer/profile.html", customer=customer)


@bp.route("/measurements", methods=["GET", "POST"])
@customer_login_required
def measurements():
    customer = current_customer()
    first_time = request.args.get("first_time")

    if request.method == "POST":
        errors = []
        new_version = save_new_measurement_version(customer["id"], request.form, errors)

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("customer/measurements.html", customer=customer,
                                    fields=MEASUREMENT_FIELDS, current=None, versions=[],
                                    form_values=request.form, first_time=first_time)

        flash(f"Measurement saved (version {new_version}).", "success")
        if first_time:
            return redirect(url_for("public.designs"))
        return redirect(url_for("customer.measurements"))

    current = db.query(
        "SELECT * FROM measurements WHERE customer_id = ? AND is_current = 1",
        (customer["id"],), one=True,
    )
    versions = db.query(
        "SELECT * FROM measurements WHERE customer_id = ? ORDER BY version DESC",
        (customer["id"],),
    )
    return render_template("customer/measurements.html", customer=customer,
                            fields=MEASUREMENT_FIELDS, current=current, versions=versions,
                            form_values=dict(current) if current else {}, first_time=first_time)


@bp.route("/order/new/<int:design_id>", methods=["GET", "POST"])
@customer_login_required
def new_order(design_id):
    customer = current_customer()
    design = db.query("SELECT * FROM designs WHERE id = ? AND status = 'ACTIVE'",
                       (design_id,), one=True)
    if not design:
        flash("This design is not available.", "danger")
        return redirect(url_for("public.designs"))

    measurement = db.query(
        "SELECT * FROM measurements WHERE customer_id = ? AND is_current = 1",
        (customer["id"],), one=True,
    )
    if not measurement:
        flash("Please add your measurements before placing an order.", "warning")
        return redirect(url_for("customer.measurements", first_time=1))

    total_amount = (design["base_price"] or 0) + (design["additional_charges"] or 0)

    if request.method == "POST":
        customisation_notes = request.form.get("customisation_notes", "").strip()
        delivery_date_str = request.form.get("delivery_date", "").strip()
        payment_mode = request.form.get("payment_mode", "AT_SHOP")

        errors = []
        try:
            delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
            if delivery_date < date.today():
                errors.append("Delivery date cannot be before today.")  # BR-019
        except ValueError:
            errors.append("Please choose a valid delivery date.")
            delivery_date = None

        if delivery_date:
            capacity = current_app.config["MAX_ORDERS_PER_DAY"]
            booked = db.query(
                "SELECT COUNT(*) c FROM orders WHERE delivery_date = ? AND status != 'CANCELLED'",
                (delivery_date.isoformat(),), one=True,
            )["c"]
            if booked >= capacity:
                errors.append(f"{delivery_date.isoformat()} is fully booked. Please pick another date.")

        if payment_mode not in ("ONLINE", "AT_SHOP", "AFTER_DELIVERY"):
            errors.append("Invalid payment option.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("customer/new_order.html", design=design,
                                    measurement=measurement, total_amount=total_amount)

        order_number = generate_order_number()
        payment_status = "PENDING"
        order_id = db.execute(
            """INSERT INTO orders
               (order_number, customer_id, design_id, measurement_id, customisation_notes,
                total_amount, amount_received, amount_pending, payment_mode, payment_status,
                delivery_date, status)
               VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 'ORDER_RECEIVED')""",
            (order_number, customer["id"], design["id"], measurement["id"], customisation_notes or None,
             total_amount, total_amount, payment_mode, payment_status, delivery_date.isoformat()),
        )
        db.execute(
            """INSERT INTO order_status_history (order_id, previous_status, new_status, remarks, updated_by)
               VALUES (?, NULL, 'ORDER_RECEIVED', 'Order placed by customer', ?)""",
            (order_id, customer["mobile"]),
        )

        # Automatic "order received" confirmation email - only fires if
        # ORDER_RECEIVED is enabled in Admin > Settings > Email Triggers.
        # This is the single order-creation path for both self-service
        # customer orders and orders placed using a measurement the admin
        # took for the customer earlier - admin doesn't create orders
        # directly, so this one hook covers both cases from the request.
        send_status_email({"id": order_id, "order_number": order_number}, customer, "ORDER_RECEIVED")

        flash(f"Order {order_number} placed successfully!", "success")
        return redirect(url_for("customer.order_detail", order_number=order_number))

    return render_template("customer/new_order.html", design=design, measurement=measurement,
                            total_amount=total_amount)


@bp.route("/orders")
@customer_login_required
def orders():
    customer = current_customer()
    rows = db.query(
        """SELECT o.*, d.name as design_name FROM orders o
           JOIN designs d ON d.id = o.design_id
           WHERE o.customer_id = ? ORDER BY o.created_at DESC""",
        (customer["id"],),
    )
    return render_template("customer/orders.html", orders=rows)


@bp.route("/order/<order_number>")
@customer_login_required
def order_detail(order_number):
    customer = current_customer()
    # BR-012 / Security Section 35: customer can only view their own orders
    order = db.query(
        """SELECT o.*, d.name as design_name, d.image_path as design_image
           FROM orders o JOIN designs d ON d.id = o.design_id
           WHERE o.order_number = ? AND o.customer_id = ?""",
        (order_number, customer["id"]), one=True,
    )
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("customer.orders"))

    history = db.query(
        "SELECT * FROM order_status_history WHERE order_id = ? ORDER BY created_at",
        (order["id"],),
    )
    trial_images = db.query(
        "SELECT * FROM order_images WHERE order_id = ? AND image_type = 'Trial' AND is_active = 1 "
        "ORDER BY uploaded_at DESC",
        (order["id"],),
    )
    payments = db.query("SELECT * FROM payments WHERE order_id = ? ORDER BY created_at", (order["id"],))
    return render_template("customer/order_detail.html", order=order, history=history,
                            trial_images=trial_images, payments=payments)


@bp.route("/order/<order_number>/reference-image", methods=["POST"])
@customer_login_required
def upload_reference_image(order_number):
    customer = current_customer()
    order = db.query("SELECT * FROM orders WHERE order_number = ? AND customer_id = ?",
                      (order_number, customer["id"]), one=True)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("customer.orders"))

    file = request.files.get("image")
    try:
        file_name, file_path = save_image(file, "CustomerReference", f"CUST{customer['id']:06d}",
                                           uploaded_by=customer["mobile"])
        db.execute(
            """INSERT INTO order_images (order_id, customer_id, image_type, file_name, file_path, uploaded_by)
               VALUES (?, ?, 'CustomerReference', ?, ?, ?)""",
            (order["id"], customer["id"], file_name, file_path, customer["mobile"]),
        )
        flash("Reference image uploaded.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("customer.order_detail", order_number=order_number))
