"""
Database models for the LG Store Python rewrite.

Tables:
- Category    -> product categories with names in all 3 languages
- Product     -> catalog items (name, category, price, description, rating, stock)
- ProductImage-> multiple images per product (gallery, not just one picture)
- Customer    -> registered shoppers (email + hashed password + profile photo)
- Address     -> saved delivery addresses for a customer (a customer can have several)
- Order       -> a checkout/order placed by a customer (cash or transfer)
- OrderItem   -> individual product lines inside an order
- Review      -> customer feedback left on a product
- Wishlist    -> products a customer has saved/favorited
- AdminUser   -> reserved for future DB-backed admin accounts

Store contact info (address/phone) is a single fixed store, so it lives
in backend/config.py as STORE_INFO rather than its own table.
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

class Category(db.Model):
    """
    Product categories, stored once with translated names, rather than a
    free-text string repeated on every product. This is how a real catalog
    is normally modeled - it keeps category names consistent and makes it
    possible to rename/translate a whole category in one place.
    """
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)  # e.g. "tv", "refrigerator"
    name_en = db.Column(db.String(80), nullable=False)
    name_ru = db.Column(db.String(80), nullable=False)
    name_tk = db.Column(db.String(80), nullable=False)
    icon = db.Column(db.String(10))  # a small emoji/icon shown in category filters

    products = db.relationship("Product", backref="category_obj", lazy=True)

    def localized_name(self, lang):
        return {"en": self.name_en, "ru": self.name_ru, "tk": self.name_tk}.get(lang, self.name_en)

    @staticmethod
    def get_all():
        return Category.query.order_by(Category.name_en).all()

    @staticmethod
    def get_by_slug(slug):
        return Category.query.filter_by(slug=slug).first()


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(20), unique=True)  # human-readable code, e.g. "LG-0001"
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    price = db.Column(db.Numeric(10, 2))
    description = db.Column(db.Text)
    quality_rating = db.Column(db.Float, default=0.0)   # average rating, cached from reviews
    stock_qty = db.Column(db.Integer, default=100)       # simple inventory count
    is_featured = db.Column(db.Boolean, default=False)   # shown in the "Best Sellers" section
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviews = db.relationship("Review", backref="product", lazy=True,
                               cascade="all, delete-orphan")
    images = db.relationship("ProductImage", backref="product", lazy=True,
                              cascade="all, delete-orphan",
                              order_by="ProductImage.sort_order")

    @property
    def category(self):
        """Backward-compatible plain string accessor (old templates use product.category)."""
        return self.category_obj.name_en if self.category_obj else None

    @property
    def primary_image(self):
        """The main image shown on cards/thumbnails - first image in the gallery."""
        return self.images[0].image_url if self.images else "https://placehold.co/400x300?text=No+Image"

    @property
    def image_url(self):
        """Backward-compatible alias so existing templates keep working."""
        return self.primary_image

    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "category": self.category,
            "price": float(self.price) if self.price is not None else None,
            "image_url": self.primary_image,
            "description": self.description,
            "quality_rating": self.quality_rating,
            "stock_qty": self.stock_qty,
        }

    def recalc_rating(self):
        """Recompute the cached average rating from all reviews on this product."""
        if not self.reviews:
            self.quality_rating = 0.0
            return
        self.quality_rating = round(
            sum(r.rating for r in self.reviews) / len(self.reviews), 1
        )

    # ---- Query helpers ----

    @staticmethod
    def get_all():
        return Product.query.order_by(Product.id.desc()).all()

    @staticmethod
    def get_by_id(product_id):
        return Product.query.get(product_id)

    @staticmethod
    def get_by_category_slug(slug):
        return (
            Product.query.join(Category)
            .filter(Category.slug == slug)
            .order_by(Product.id.desc())
            .all()
        )

    @staticmethod
    def search(keyword):
        like_pattern = f"%{keyword.lower()}%"
        return (
            Product.query.filter(db.func.lower(Product.name).like(like_pattern))
            .order_by(Product.id.desc())
            .all()
        )

    @staticmethod
    def get_featured(limit=4):
        return (
            Product.query.filter_by(is_featured=True)
            .order_by(Product.id.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def next_sku():
        """Generate the next SKU like LG-0013 based on current row count."""
        count = Product.query.count()
        return f"LG-{count + 1:04d}"


class ProductImage(db.Model):
    """
    A single image belonging to a product's gallery. Splitting this into its
    own table (instead of one image_url column) lets a product have several
    photos, shown as a gallery/carousel on the product page - like a real
    e-commerce catalog.
    """
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    sort_order = db.Column(db.Integer, default=0)


# ---------------------------------------------------------------------------
# Customers & profile
# ---------------------------------------------------------------------------

class Customer(db.Model):
    """A registered shopper. Logs in with email + password (separate from admin)."""
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30))
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.String(500))            # profile photo, editable any time
    date_of_birth = db.Column(db.Date)
    preferred_lang = db.Column(db.String(5), default="tk")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = db.relationship("Order", backref="customer", lazy=True)
    reviews = db.relationship("Review", backref="customer", lazy=True)
    addresses = db.relationship("Address", backref="customer", lazy=True,
                                 cascade="all, delete-orphan")
    wishlist_items = db.relationship("Wishlist", backref="customer", lazy=True,
                                      cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def initials(self):
        """Fallback shown instead of an avatar image when no photo is set."""
        parts = self.full_name.split()
        letters = "".join(p[0] for p in parts[:2] if p)
        return letters.upper() or "?"

    @staticmethod
    def get_by_email(email):
        return Customer.query.filter_by(email=email.lower().strip()).first()

    @staticmethod
    def get_by_id(customer_id):
        return Customer.query.get(customer_id)


class Address(db.Model):
    """
    A saved delivery address for a customer. A customer can have more than
    one (home, work, etc.) - a real store profile normally supports this
    instead of a single free-text field.
    """
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    label = db.Column(db.String(50))           # e.g. "Home", "Work"
    city = db.Column(db.String(100))
    street_address = db.Column(db.String(255))
    is_default = db.Column(db.Boolean, default=False)

    @staticmethod
    def get_for_customer(customer_id):
        return Address.query.filter_by(customer_id=customer_id).all()


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class Order(db.Model):
    """
    A checkout / placed order. Payment is settled offline (cash on pickup,
    or phone/bank transfer) after the customer contacts the seller directly.
    """
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True)  # human-readable, e.g. "ORD-2026-0001"
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)   # 'cash' or 'transfer'
    status = db.Column(db.String(20), default="pending")        # pending/confirmed/completed/cancelled
    contact_phone = db.Column(db.String(30))                     # phone customer wants to be reached on
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True,
                             cascade="all, delete-orphan")

    @staticmethod
    def get_by_id(order_id):
        return Order.query.get(order_id)

    @staticmethod
    def get_for_customer(customer_id):
        return (
            Order.query.filter_by(customer_id=customer_id)
            .order_by(Order.created_at.desc())
            .all()
        )

    @staticmethod
    def get_all():
        """Used by the admin dashboard to see every order across all customers."""
        return Order.query.order_by(Order.created_at.desc()).all()

    @staticmethod
    def next_order_number():
        year = datetime.utcnow().year
        count = Order.query.count()
        return f"ORD-{year}-{count + 1:04d}"


class OrderItem(db.Model):
    """One product line within an order (product + quantity + price at time of purchase)."""
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)  # snapshot, survives product edits/deletes
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    product = db.relationship("Product")

    @property
    def subtotal(self):
        return float(self.unit_price) * self.quantity


class Review(db.Model):
    """Customer feedback left on a product (rating 1-5 + comment)."""
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def get_for_product(product_id):
        return (
            Review.query.filter_by(product_id=product_id)
            .order_by(Review.created_at.desc())
            .all()
        )


class Wishlist(db.Model):
    """Products a customer has saved/favorited for later - common on real
    e-commerce sites, gives the profile page more substance than a bare
    order history."""
    __tablename__ = "wishlist_items"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship("Product")

    @staticmethod
    def get_for_customer(customer_id):
        return Wishlist.query.filter_by(customer_id=customer_id).all()

    @staticmethod
    def exists(customer_id, product_id):
        return Wishlist.query.filter_by(customer_id=customer_id, product_id=product_id).first() is not None


class AdminUser(db.Model):
    """Reserved for future DB-backed admin accounts (current admin login is
    config-based, see backend/auth.py)."""
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
