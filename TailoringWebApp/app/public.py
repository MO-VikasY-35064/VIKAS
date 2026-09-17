from flask import Blueprint, render_template, request

from . import db
from .utils import ORDER_STATUS_FLOW

bp = Blueprint("public", __name__)


@bp.route("/")
def home():
    designs = db.query(
        "SELECT * FROM designs WHERE status = 'ACTIVE' ORDER BY created_at DESC"
    )
    gallery = db.query(
        "SELECT * FROM gallery WHERE is_active = 1 ORDER BY display_order"
    )
    return render_template("public/home.html", designs=designs, gallery=gallery)


@bp.route("/designs")
def designs():
    category = request.args.get("category", "").strip()
    if category:
        rows = db.query(
            "SELECT * FROM designs WHERE status='ACTIVE' AND category = ? ORDER BY created_at DESC",
            (category,),
        )
    else:
        rows = db.query("SELECT * FROM designs WHERE status='ACTIVE' ORDER BY created_at DESC")
    categories = db.query(
        "SELECT DISTINCT category FROM designs WHERE status='ACTIVE' AND category IS NOT NULL"
    )
    return render_template("public/designs.html", designs=rows, categories=categories,
                            selected_category=category)


@bp.route("/gallery")
def gallery():
    rows = db.query("SELECT * FROM gallery WHERE is_active = 1 ORDER BY display_order")
    return render_template("public/gallery.html", gallery=rows)


@bp.route("/pricing")
def pricing():
    rows = db.query("SELECT * FROM designs WHERE status='ACTIVE' ORDER BY base_price")
    return render_template("public/pricing.html", designs=rows)


@bp.route("/how-it-works")
def how_it_works():
    return render_template("public/how_it_works.html")


@bp.route("/contact")
def contact():
    return render_template("public/contact.html")


@bp.route("/track-order", methods=["GET", "POST"])
def track_order():
    order = None
    history = []
    searched = False
    if request.method == "POST":
        searched = True
        order_number = request.form.get("order_number", "").strip().upper()
        order = db.query(
            """SELECT o.*, d.name as design_name, c.name as customer_name
               FROM orders o
               JOIN designs d ON d.id = o.design_id
               JOIN customers c ON c.id = o.customer_id
               WHERE o.order_number = ?""",
            (order_number,), one=True,
        )
        if order:
            history = db.query(
                "SELECT * FROM order_status_history WHERE order_id = ? ORDER BY created_at",
                (order["id"],),
            )
    return render_template("public/track_order.html", order=order, history=history,
                            searched=searched, status_flow=ORDER_STATUS_FLOW)
