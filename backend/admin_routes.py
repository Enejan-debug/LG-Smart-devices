"""
Admin / developer-only routes.

Equivalent to: AdminLoginServlet.java, LogoutServlet.java, ProductServlet.java,
ProductEditServlet.java, product-list.jsp, add-product.jsp, edit-product.jsp.

Every route in this blueprint (except /admin/login) is protected by
admin_login_required, so a customer can NEVER reach product management,
no matter what URL they type - they'll just get bounced to the admin
login page. This mirrors the original project's
`if (session.getAttribute("isAdmin") == null) redirect to admin-login.jsp`
checks in every admin JSP.
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app,
)

from .extensions import db
from .models import Product, ProductImage, Category, Order
from .auth import login_admin, logout_admin, is_admin_logged_in, admin_login_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if is_admin_logged_in():
        return redirect(url_for("admin.product_list"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (username == current_app.config["ADMIN_USERNAME"]
                and password == current_app.config["ADMIN_PASSWORD"]):
            login_admin()
            return redirect(url_for("admin.product_list"))

        flash("Invalid username or password.", "error")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    logout_admin()
    return redirect(url_for("store.home"))


@admin_bp.route("/products")
@admin_login_required
def product_list():
    products = Product.get_all()
    return render_template("admin/product_list.html", products=products)


@admin_bp.route("/products/add", methods=["GET", "POST"])
@admin_login_required
def product_add():
    if request.method == "POST":
        try:
            product = Product(
                sku=Product.next_sku(),
                name=request.form["name"].strip(),
                category_id=int(request.form["category_id"]),
                price=float(request.form["price"]),
                description=request.form.get("description", "").strip(),
                stock_qty=int(request.form.get("stock_qty", 100) or 100),
                is_featured=bool(request.form.get("is_featured")),
            )
            db.session.add(product)
            db.session.flush()  # get product.id for the images below

            image_urls = [
                line.strip() for line in request.form.get("image_urls", "").splitlines()
                if line.strip()
            ]
            for order, img_url in enumerate(image_urls):
                db.session.add(ProductImage(product_id=product.id, image_url=img_url, sort_order=order))

            db.session.commit()
            flash("Product added successfully.", "success")
            return redirect(url_for("admin.product_list"))
        except (KeyError, ValueError):
            flash("Could not add product. Please check the values and try again.", "error")

    return render_template("admin/product_form.html", product=None, categories=Category.get_all())


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_login_required
def product_edit(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("admin.product_list"))

    if request.method == "POST":
        try:
            product.name = request.form["name"].strip()
            product.category_id = int(request.form["category_id"])
            product.price = float(request.form["price"])
            product.description = request.form.get("description", "").strip()
            product.stock_qty = int(request.form.get("stock_qty", product.stock_qty) or 0)
            product.is_featured = bool(request.form.get("is_featured"))

            # Replace the whole image gallery with whatever was submitted -
            # simplest way to let the admin reorder/add/remove images at once.
            ProductImage.query.filter_by(product_id=product.id).delete()
            image_urls = [
                line.strip() for line in request.form.get("image_urls", "").splitlines()
                if line.strip()
            ]
            for order, img_url in enumerate(image_urls):
                db.session.add(ProductImage(product_id=product.id, image_url=img_url, sort_order=order))

            db.session.commit()
            flash("Product updated successfully.", "success")
            return redirect(url_for("admin.product_list"))
        except (KeyError, ValueError):
            flash("Could not update product. Please check the values and try again.", "error")

    return render_template("admin/product_form.html", product=product, categories=Category.get_all())


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_login_required
def product_delete(product_id):
    product = Product.get_by_id(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted.", "success")
    return redirect(url_for("admin.product_list"))


@admin_bp.route("/orders")
@admin_login_required
def order_list():
    """Lets the developer/store owner see every order placed by every customer."""
    orders = Order.get_all()
    return render_template("admin/order_list.html", orders=orders)


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_login_required
def order_update_status(order_id):
    order = Order.get_by_id(order_id)
    new_status = request.form.get("status", "").strip()

    if order and new_status in ("pending", "confirmed", "completed", "cancelled"):
        order.status = new_status
        db.session.commit()
        flash(f"Order #{order.id} marked as {new_status}.", "success")

    return redirect(url_for("admin.order_list"))
