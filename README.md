# LG Store - Python (Flask) Rewrite

A full rewrite of the original Java EE (Servlet/JSP) LG Store project in
Python, using Flask. No Eclipse, no Tomcat, no Java installation needed -
just Python and VS Code.

## What this project does

**Customers** (public / no login needed to browse):
- Browse, search, and filter the product catalog
- View product details, ratings, and customer feedback

**Customers** (after registering / logging in with email + password):
- Add products to a cart, update quantities, remove items
- Checkout: place a real order (cash on pickup or phone/bank transfer)
- View their own order history on "My Account"
- Leave a star rating + written feedback on any product
- Call the store directly (real `tel:` link, phone number pulled from
  the store's contact info) to arrange payment/pickup before or after ordering

**Admin / developer** (separate login, `/admin/login`):
- Add, edit, delete products (name, category, price, stock, image, description)
- View every order placed by every customer
- Update an order's status (pending -> confirmed -> completed / cancelled)

A customer account can never reach the admin panel, and the admin login
has no access to customer accounts - these are two completely separate
authentication systems (see `backend/auth.py`).

## Project structure

```
lgstore_python/
├── app.py                     <- entry point, run this file
├── requirements.txt
├── backend/                   <- ALL backend logic (Python, not visible to customers)
│   ├── __init__.py            <- Flask app factory
│   ├── config.py              <- DB connection, admin credentials, store contact info
│   ├── extensions.py          <- shared SQLAlchemy instance
│   ├── models.py               <- Product, Customer, Order, OrderItem, Review, AdminUser
│   ├── auth.py                <- customer login + admin login (kept fully separate)
│   ├── store_routes.py        <- public + customer routes (browse/cart/checkout/reviews)
│   ├── admin_routes.py        <- admin-only routes (product & order management)
│   └── seed.py                <- inserts the starter LG catalog on first run
├── templates/                 <- customer-facing HTML (Jinja2)
│   ├── base.html, index.html, product.html
│   ├── login.html, register.html, account.html
│   ├── cart.html, checkout.html, order_confirmation.html
│   └── admin/                 <- admin-only HTML, never linked from customer pages
│       ├── base_admin.html, login.html
│       ├── product_list.html, product_form.html, order_list.html
└── static/
    └── css/style.css          <- one shared stylesheet for the whole site
```

## ⚠️ Important: delete the old database before first run

If you have an existing `lgstore.db` file from a previous version of this
project, **delete it** before running `python app.py` again. The database
only seeds itself once - if `lgstore.db` already exists with old data
(old product names, old prices, old seller info), the app will keep using
that old data instead of the updated catalog below.

```
# From inside the lgstore_python folder:
del lgstore.db         (Windows)
rm lgstore.db           (macOS/Linux)
```

Then run `python app.py` again - it will recreate the database with the
correct products, prices, and seller info automatically.

## What's new in this version

- **Real LG product catalog** - actual current model names (LG OLED evo C5,
  LG InstaView refrigerator, LG WashTower, etc.) with detailed descriptions
  and a facts table (SKU, category, stock, brand, warranty) on every product page.
- **Prices in Turkmenistani manat (TMT)** instead of US dollars.
- **Category illustrations** for every product (TV, refrigerator, washer, AC,
  air purifier, laptop, monitor, speaker, microwave) stored locally in
  `static/images/products/` - no external links, so images always load.
- **3 languages: Turkmen (default), Russian, English** - switch anytime using
  the TK / RU / EN links in the top-right of the navbar. Turkmen is the
  default across both the customer storefront and the admin dashboard, since
  this site is built primarily for use in Turkmenistan.
- **Updated seller contact info** - address, phone, and hours are set in
  `backend/config.py` under `STORE_INFO` and shown on every product page,
  checkout page, and the site footer.
- **"Best Sellers" homepage section** - a red-and-white highlighted block at
  the top of the homepage showing hand-picked products. Mark any product as
  a best-seller by checking "Show in Best Sellers" on its Add/Edit form in
  the admin panel. Hidden automatically while the customer is searching or
  filtering by category.

## How to change/add products

You don't need to touch any code to manage products:

1. Go to `/admin/login` and log in (default: `admin` / `admin123`)
2. **Add a product**: click "+ Add New Product", fill in name, category,
   price (in TMT), stock, an image URL, and a description
3. **Edit a product**: click "Edit" next to any product in the list
4. **Delete a product**: click "Delete" next to any product in the list
5. **Feature a product on the homepage**: check the "Show in Best Sellers"
   box on the Add/Edit form

If you'd rather edit the starter catalog in code instead, it lives in
`backend/seed.py` - but remember this only runs once on an empty database,
so delete `lgstore.db` after editing it (see the warning above).

## How to run in VS Code

1. Open this folder (`lgstore_python`) in VS Code.
2. Open a terminal in VS Code (`Terminal > New Terminal`).
3. (Recommended) create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS/Linux
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the app:
   ```
   python app.py
   ```
6. Open your browser at: **http://127.0.0.1:5000**

That's it - no Tomcat, no Eclipse project configuration, no JDK version
conflicts. The database (SQLite file `lgstore.db`) is created and seeded
with the starter catalog automatically the first time you run it.

## Logins for testing

- **Admin panel:** go to `/admin/login` → username `admin`, password `admin123`
  (change these in `backend/config.py` before deploying anywhere real)
- **Test customer:** email `test@example.com`, password `test123` (created
  automatically on first run - see `backend/seed.py`)
- **Or register your own account** at `/register` with any email/password you like -
  each customer sets their own password, which is stored securely (hashed, never
  in plain text)

## Store contact info (shown to customers)

Edit `STORE_INFO` in `backend/config.py` to set your real store name,
address, phone number, email, and hours. This is what powers the
"Call Seller" buttons and the footer on every page.

## Switching from SQLite to MySQL (optional)

By default this uses a local SQLite file so it runs with zero setup.
If you'd rather use MySQL (like the original Java project):

1. `pip install pymysql`
2. In `backend/config.py`, replace the `SQLALCHEMY_DATABASE_URI` line with:
   ```python
   SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:your_password@localhost:3306/lgstore"
   ```
3. Create the `lgstore` database in MySQL first (an empty `CREATE DATABASE lgstore;` is enough - tables are created automatically).

## Notes

- Every button in this project (Add to Cart, Checkout, Place Order, Login,
  Register, Submit Feedback, Call, admin Add/Edit/Delete/Update Status) is
  wired to a real backend route - nothing is decorative.
- Payment is handled offline (cash on pickup or phone/bank transfer) - there
  is no payment gateway integration, matching what was requested.
