"""
Authentication helpers.

Two completely separate login systems, on purpose:
- Customer auth  -> email + password, stored in the `customers` table,
                    session key "customer_id". Used for shopping/checkout/reviews.
- Admin auth     -> username + password checked against Config values,
                    session key "is_admin". Used for the product management panel.

Keeping them separate means a customer account can NEVER accidentally
get admin/management access, and vice versa.
"""
from functools import wraps
from flask import session, redirect, url_for, request, flash

from .models import Customer


# ---------------- Customer auth ----------------

def login_customer(customer: Customer):
    session["customer_id"] = customer.id
    session["customer_name"] = customer.full_name


def logout_customer():
    session.pop("customer_id", None)
    session.pop("customer_name", None)


def current_customer():
    """Returns the logged-in Customer object, or None if not logged in."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return None
    return Customer.query.get(customer_id)


def customer_login_required(view_func):
    """Decorator: redirects to /login if no customer is logged in.
    Used to protect cart, checkout, and review-submission routes."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("customer_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("store.login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


# ---------------- Admin auth ----------------

def login_admin():
    session["is_admin"] = True


def logout_admin():
    session.pop("is_admin", None)


def is_admin_logged_in():
    return session.get("is_admin") is True


def admin_login_required(view_func):
    """Decorator: redirects to the admin login page if not authenticated as admin."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not is_admin_logged_in():
            return redirect(url_for("admin.login"))
        return view_func(*args, **kwargs)
    return wrapped
