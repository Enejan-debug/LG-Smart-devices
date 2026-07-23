"""
Customer-facing routes - PUBLIC (browsing) + customer-account-gated
(cart, checkout, reviews).

A customer can:
  - browse/search/filter products                (no login needed)
  - view a product detail page + read reviews     (no login needed)
  - register / log in / log out                   -> creates a Customer session
  - add items to a cart (stored in the session)
  - check out -> creates a real Order + OrderItems in the database
  - leave a review/feedback on a product they've ordered
  - see their own order history
  - call the store directly (tel: link, rendered from STORE_INFO)

There is NO way for a customer to reach product-management (add/edit/delete
products) from anywhere in this blueprint - that logic only exists in
admin_routes.py behind admin_login_required.
"""
from decimal import Decimal
import os
import uuid

from werkzeug.utils import secure_filename
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash,
    current_app,
)

from .extensions import db
from .models import Product, Customer, Order, OrderItem, Review, Category, Address, Wishlist
from .auth import (
    login_customer, logout_customer, current_customer,
    customer_login_required,
)

store_bp = Blueprint("store", __name__)

ALLOWED_AVATAR_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _allowed_avatar_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS


# ---------------- Language switch ----------------

@store_bp.route("/set-language/<lang_code>")
def set_language(lang_code):
    from .translations import SUPPORTED_LANGS
    if lang_code in SUPPORTED_LANGS:
        session["lang"] = lang_code
    return redirect(request.referrer or url_for("store.home"))


# ---------------- Browsing (public) ----------------

@store_bp.route("/")
def home():
    keyword = request.args.get("keyword", "").strip()
    category_slug = request.args.get("category", "").strip()

    categories = Category.get_all()

    if keyword:
        products = Product.search(keyword)
    elif category_slug:
        products = Product.get_by_category_slug(category_slug)
    else:
        products = Product.get_all()

    # "Best Sellers" section only makes sense on the unfiltered homepage -
    # hide it once the customer is searching or filtering by category.
    featured = Product.get_featured() if not keyword and not category_slug else []

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        keyword=keyword,
        selected_category=category_slug,
        featured=featured,
        customer=current_customer(),
        store_info=current_app.config["STORE_INFO"],
    )


@store_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.get_by_id(product_id)
    reviews = Review.get_for_product(product_id) if product else []
    customer = current_customer()
    is_wishlisted = (
        Wishlist.query.filter_by(customer_id=customer.id, product_id=product_id).first() is not None
        if customer else False
    )
    return render_template(
        "product.html",
        product=product,
        reviews=reviews,
        customer=customer,
        is_wishlisted=is_wishlisted,
        store_info=current_app.config["STORE_INFO"],
    )


# ---------------- Customer registration / login / logout ----------------

@store_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        error = None
        if not full_name or not email or not password:
            error = "Name, email, and password are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif Customer.get_by_email(email):
            error = "An account with this email already exists."

        if error:
            flash(error, "error")
            return render_template("register.html", form=request.form)

        customer = Customer(full_name=full_name, email=email, phone=phone)
        customer.set_password(password)
        db.session.add(customer)
        db.session.commit()

        login_customer(customer)
        flash("Account created successfully. Welcome!", "success")
        return redirect(url_for("store.home"))

    return render_template("register.html", form={})


@store_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        customer = Customer.get_by_email(email)
        if customer and customer.check_password(password):
            login_customer(customer)
            flash(f"Welcome back, {customer.full_name}!", "success")
            next_url = request.args.get("next") or url_for("store.home")
            return redirect(next_url)

        flash("Invalid email or password.", "error")
        return render_template("login.html", email=email)

    return render_template("login.html", email="")


@store_bp.route("/logout")
def logout():
    logout_customer()
    flash("You have been logged out.", "success")
    return redirect(url_for("store.home"))


@store_bp.route("/account")
@customer_login_required
def account():
    customer = current_customer()
    orders = Order.get_for_customer(customer.id)
    wishlist = Wishlist.get_for_customer(customer.id)
    return render_template(
        "account.html",
        customer=customer,
        orders=orders,
        wishlist=wishlist,
        store_info=current_app.config["STORE_INFO"],
    )


@store_bp.route("/account/edit", methods=["GET", "POST"])
@customer_login_required
def account_edit():
    """
    Lets a customer update their own profile at any time - name, phone,
    date of birth, preferred language, and saved address. Email is kept
    read-only here since it's also the login identifier.
    """
    customer = current_customer()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        dob = request.form.get("date_of_birth", "").strip()
        city = request.form.get("city", "").strip()
        street_address = request.form.get("street_address", "").strip()

        if not full_name:
            flash("Name cannot be empty.", "error")
            return redirect(url_for("store.account_edit"))

        customer.full_name = full_name
        customer.phone = phone

        if dob:
            from datetime import datetime as _dt
            try:
                customer.date_of_birth = _dt.strptime(dob, "%Y-%m-%d").date()
            except ValueError:
                pass

        # Keep a single default address per customer, simple and editable any time.
        existing = Address.query.filter_by(customer_id=customer.id, is_default=True).first()
        if not existing:
            existing = Address(customer_id=customer.id, is_default=True, label="Home")
            db.session.add(existing)
        existing.city = city
        existing.street_address = street_address

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("store.account"))

    address = Address.query.filter_by(customer_id=customer.id, is_default=True).first()
    return render_template(
        "account_edit.html",
        customer=customer,
        address=address,
        store_info=current_app.config["STORE_INFO"],
    )


@store_bp.route("/account/avatar", methods=["POST"])
@customer_login_required
def account_avatar_upload():
    """Uploads/replaces the customer's profile photo. Can be changed again
    at any time by simply uploading a new file."""
    customer = current_customer()
    file = request.files.get("avatar")

    if not file or file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("store.account_edit"))

    if not _allowed_avatar_file(file.filename):
        flash("Please upload an image file (png, jpg, jpeg, gif, or webp).", "error")
        return redirect(url_for("store.account_edit"))

    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"customer_{customer.id}_{uuid.uuid4().hex[:8]}.{ext}"

    upload_dir = os.path.join(current_app.static_folder, "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, unique_name))

    customer.avatar_url = f"/static/uploads/avatars/{unique_name}"
    db.session.commit()

    flash("Profile photo updated.", "success")
    return redirect(url_for("store.account_edit"))


# ---------------- Wishlist ----------------

@store_bp.route("/wishlist/toggle/<int:product_id>", methods=["POST"])
@customer_login_required
def wishlist_toggle(product_id):
    customer = current_customer()
    existing = Wishlist.query.filter_by(customer_id=customer.id, product_id=product_id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Removed from your wishlist.", "success")
    else:
        db.session.add(Wishlist(customer_id=customer.id, product_id=product_id))
        db.session.commit()
        flash("Added to your wishlist.", "success")

    return redirect(request.referrer or url_for("store.home"))


# ---------------- Cart (stored in the session) ----------------

def _get_cart():
    """Cart shape: {"<product_id>": quantity}. Kept in the Flask session
    so each browser/customer has their own independent cart."""
    return session.get("cart", {})


def _save_cart(cart):
    session["cart"] = cart
    session.modified = True


@store_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("store.home"))

    quantity = max(1, int(request.form.get("quantity", 1)))

    cart = _get_cart()
    key = str(product_id)
    cart[key] = cart.get(key, 0) + quantity
    _save_cart(cart)

    flash(f"Added {quantity} x {product.name} to your cart.", "success")
    return redirect(request.referrer or url_for("store.home"))


@store_bp.route("/cart")
def cart_view():
    cart = _get_cart()
    items = []
    total = Decimal("0.00")

    for product_id_str, qty in cart.items():
        product = Product.get_by_id(int(product_id_str))
        if not product:
            continue
        subtotal = Decimal(str(product.price)) * qty
        total += subtotal
        items.append({"product": product, "quantity": qty, "subtotal": subtotal})

    return render_template(
        "cart.html",
        items=items,
        total=total,
        customer=current_customer(),
        store_info=current_app.config["STORE_INFO"],
    )


@store_bp.route("/cart/update/<int:product_id>", methods=["POST"])
def cart_update(product_id):
    cart = _get_cart()
    key = str(product_id)
    new_qty = int(request.form.get("quantity", 1))

    if new_qty <= 0:
        cart.pop(key, None)
    else:
        cart[key] = new_qty

    _save_cart(cart)
    return redirect(url_for("store.cart_view"))


@store_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
def cart_remove(product_id):
    cart = _get_cart()
    cart.pop(str(product_id), None)
    _save_cart(cart)
    flash("Item removed from cart.", "success")
    return redirect(url_for("store.cart_view"))


# ---------------- Checkout (requires customer login) ----------------

@store_bp.route("/checkout", methods=["GET", "POST"])
@customer_login_required
def checkout():
    cart = _get_cart()
    if not cart:
        flash("Your cart is empty.", "error")
        return redirect(url_for("store.home"))

    customer = current_customer()

    items = []
    total = Decimal("0.00")
    for product_id_str, qty in cart.items():
        product = Product.get_by_id(int(product_id_str))
        if not product:
            continue
        subtotal = Decimal(str(product.price)) * qty
        total += subtotal
        items.append({"product": product, "quantity": qty, "subtotal": subtotal})

    if request.method == "POST":
        payment_method = request.form.get("payment_method", "cash")
        contact_phone = request.form.get("contact_phone", "").strip()
        notes = request.form.get("notes", "").strip()

        if payment_method not in ("cash", "transfer"):
            payment_method = "cash"

        order = Order(
            order_number=Order.next_order_number(),
            customer_id=customer.id,
            total_amount=total,
            payment_method=payment_method,
            contact_phone=contact_phone,
            notes=notes,
            status="pending",
        )
        db.session.add(order)
        db.session.flush()  # get order.id before commit

        for entry in items:
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=entry["product"].id,
                product_name=entry["product"].name,
                unit_price=entry["product"].price,
                quantity=entry["quantity"],
            ))

        db.session.commit()
        _save_cart({})  # empty the cart after a successful order

        flash(
            "Order placed! The seller will contact you to confirm "
            "payment (cash on pickup or transfer) and delivery.",
            "success",
        )
        return redirect(url_for("store.order_confirmation", order_id=order.id))

    return render_template(
        "checkout.html",
        items=items,
        total=total,
        customer=customer,
        store_info=current_app.config["STORE_INFO"],
    )


@store_bp.route("/order/<int:order_id>/confirmation")
@customer_login_required
def order_confirmation(order_id):
    order = Order.get_by_id(order_id)
    customer = current_customer()

    if not order or order.customer_id != customer.id:
        flash("Order not found.", "error")
        return redirect(url_for("store.home"))

    return render_template(
        "order_confirmation.html",
        order=order,
        store_info=current_app.config["STORE_INFO"],
    )


# ---------------- Reviews / feedback ----------------

@store_bp.route("/product/<int:product_id>/review", methods=["POST"])
@customer_login_required
def add_review(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("store.home"))

    customer = current_customer()

    try:
        rating = int(request.form.get("rating", 0))
    except ValueError:
        rating = 0
    comment = request.form.get("comment", "").strip()

    if rating < 1 or rating > 5:
        flash("Please choose a rating between 1 and 5.", "error")
        return redirect(url_for("store.product_detail", product_id=product_id))

    review = Review(
        product_id=product_id,
        customer_id=customer.id,
        rating=rating,
        comment=comment,
    )
    db.session.add(review)
    db.session.flush()

    product.reviews.append(review)
    product.recalc_rating()
    db.session.commit()

    flash("Thank you for your feedback!", "success")
    return redirect(url_for("store.product_detail", product_id=product_id))
