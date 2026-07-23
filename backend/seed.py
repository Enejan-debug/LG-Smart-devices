"""
Seeds the database with a realistic LG catalog (real current model names,
detailed descriptions, prices in Turkmenistani manat - TMT, and a small
image gallery per product). Only runs once, when the relevant tables are
still empty - safe to call every startup.
"""
from .extensions import db
from .models import Product, ProductImage, Category, Customer

# ---------------------------------------------------------------------------
# Categories (translated names + a small icon shown in the category filter)
# ---------------------------------------------------------------------------
STARTER_CATEGORIES = [
    dict(slug="tv", name_en="TV", name_ru="Телевизоры", name_tk="Telewizorlar", icon="📺"),
    dict(slug="refrigerator", name_en="Refrigerator", name_ru="Холодильники", name_tk="Sowadyjylar", icon="🧊"),
    dict(slug="washing-machine", name_en="Washing Machine", name_ru="Стиральные машины", name_tk="Kir ýuwujy maşynlar", icon="🌀"),
    dict(slug="air-conditioner", name_en="Air Conditioner", name_ru="Кондиционеры", name_tk="Kondisionerler", icon="❄️"),
    dict(slug="air-purifier", name_en="Air Purifier", name_ru="Очистители воздуха", name_tk="Howa arassalaýjylar", icon="🌬️"),
    dict(slug="laptop", name_en="Laptop", name_ru="Ноутбуки", name_tk="Noutbuklar", icon="💻"),
    dict(slug="monitor", name_en="Monitor", name_ru="Мониторы", name_tk="Monitorlar", icon="🖥️"),
    dict(slug="audio", name_en="Audio", name_ru="Аудио", name_tk="Audio", icon="🔊"),
    dict(slug="kitchen", name_en="Kitchen", name_ru="Кухонная техника", name_tk="Aşhana enjamlary", icon="🍽️"),
]

# Prices are given directly in TMT (1 USD ~= 3.5 TMT as reference).
# Each product lists one or more image paths - the gallery on the product
# page will show all of them.
STARTER_PRODUCTS = [
    dict(
        name='LG OLED evo C5 55" 4K Smart TV', category_slug="tv", price=4550.00,
        images=["/static/images/products/tv.svg"],
        is_featured=True,
        description=(
            "Self-lit OLED evo AI pixels deliver perfect black levels and infinite "
            "contrast. 4K resolution with a 120Hz refresh rate and the alpha 9 AI "
            "processor for sharper detail - ideal for movies, sports, and gaming. "
            "Runs webOS with built-in streaming apps (Netflix, YouTube, and more)."
        ),
    ),
    dict(
        name='LG QNED 65" 4K Smart TV', category_slug="tv", price=3500.00,
        images=["/static/images/products/tv.svg"],
        description=(
            "Quantum Dot NanoCell technology for a wider, more accurate color "
            "spectrum. Mini LED backlighting for deeper contrast than standard "
            "LED TVs. Includes webOS smart platform, voice control, and a "
            "Magic Remote."
        ),
    ),
    dict(
        name="LG InstaView Door-in-Door Refrigerator", category_slug="refrigerator", price=6650.00,
        images=["/static/images/products/refrigerator.svg"],
        is_featured=True,
        description=(
            "Knock twice on the glass to see inside without opening the door, "
            "keeping cold air in and food fresh longer. Craft Ice maker produces "
            "slow-melting round ice, and multi-air flow cooling keeps every shelf "
            "at an even temperature."
        ),
    ),
    dict(
        name="LG Bottom Freezer Refrigerator", category_slug="refrigerator", price=3850.00,
        images=["/static/images/products/refrigerator.svg"],
        description=(
            "Spacious bottom-freezer layout keeps everyday items at eye level. "
            "LG's linear compressor runs quieter and more efficiently than a "
            "standard compressor, and lasts longer under continuous use."
        ),
    ),
    dict(
        name="LG TurboWash 360 Washing Machine", category_slug="washing-machine", price=2800.00,
        images=["/static/images/products/washer.svg"],
        description=(
            "Washes a full load in under an hour thanks to TurboWash 360 jets that "
            "clean from every angle. Built-in steam technology removes up to 99.9% "
            "of common household allergens without extra detergent."
        ),
    ),
    dict(
        name="LG WashTower (Washer + Dryer Combo)", category_slug="washing-machine", price=7000.00,
        images=["/static/images/products/washer.svg"],
        is_featured=True,
        description=(
            "Stacked washer and dryer in a single unit with one centralized "
            "control panel, saving valuable floor space. AI DD technology senses "
            "fabric type and adjusts the wash motion automatically."
        ),
    ),
    dict(
        name="LG Dual Inverter Air Conditioner", category_slug="air-conditioner", price=1920.00,
        images=["/static/images/products/ac.svg"],
        description=(
            "Dual Inverter compressor delivers up to 70% energy savings compared "
            "to a standard fixed-speed compressor. Cools rooms faster while "
            "running quieter, with a 10-year compressor warranty."
        ),
    ),
    dict(
        name="LG PuriCare Air Purifier", category_slug="air-purifier", price=1220.00,
        images=["/static/images/products/air_purifier.svg"],
        description=(
            "Removes up to 99.999% of ultra-fine dust, pollen, and common indoor "
            "allergens with a multi-stage HEPA filter. Real-time air quality "
            "sensor changes color to show current air cleanliness at a glance."
        ),
    ),
    dict(
        name='LG Gram 16" Laptop', category_slug="laptop", price=5250.00,
        images=["/static/images/products/laptop.svg"],
        is_featured=True,
        description=(
            "Ultra-lightweight at just 1.2 kg, easy to carry to class or work "
            "every day. Up to 22 hours of battery life on a single charge, with "
            "an Intel Core i7 processor for smooth multitasking."
        ),
    ),
    dict(
        name='LG UltraGear 27" Gaming Monitor', category_slug="monitor", price=1400.00,
        images=["/static/images/products/monitor.svg"],
        description=(
            "165Hz refresh rate with 1ms response time keeps fast-motion gaming "
            "smooth and free of ghosting. NVIDIA G-SYNC compatible for tear-free "
            "visuals, with a QHD IPS panel for accurate color."
        ),
    ),
    dict(
        name="LG XBOOM Bluetooth Speaker", category_slug="audio", price=455.00,
        images=["/static/images/products/speaker.svg"],
        description=(
            "Portable speaker with deep, punchy bass and up to 20 hours of "
            "playback on a single charge. Splash-resistant design makes it "
            "suitable for kitchens, balconies, or outdoor gatherings."
        ),
    ),
    dict(
        name="LG NeoChef Microwave Oven", category_slug="kitchen", price=660.00,
        images=["/static/images/products/microwave.svg"],
        description=(
            "Smart Inverter technology delivers even cooking without cold or "
            "overcooked spots. EasyClean interior coating means no harsh "
            "chemical cleaners are needed - just wipe with a damp cloth."
        ),
    ),
]

# ---- Test customer account, so you can log in immediately without
#      registering a new account first. ----
TEST_CUSTOMER_EMAIL = "test@example.com"
TEST_CUSTOMER_PASSWORD = "test123"


def seed_if_empty():
    # 1) Categories first - products depend on them via foreign key.
    if Category.query.first() is None:
        for cat in STARTER_CATEGORIES:
            db.session.add(Category(**cat))
        db.session.commit()
        print(f"[seed] Inserted {len(STARTER_CATEGORIES)} categories into the database.")

    # 2) Products, each linked to its category and given a gallery of images.
    if Product.query.first() is None:
        slug_to_id = {c.slug: c.id for c in Category.query.all()}
        for item in STARTER_PRODUCTS:
            images = item.pop("images", [])
            slug = item.pop("category_slug")
            product = Product(
                sku=Product.next_sku(),
                category_id=slug_to_id.get(slug),
                **item,
            )
            db.session.add(product)
            db.session.flush()  # so product.id is available for the images below
            for order, img_url in enumerate(images):
                db.session.add(ProductImage(product_id=product.id, image_url=img_url, sort_order=order))
        db.session.commit()
        print(f"[seed] Inserted {len(STARTER_PRODUCTS)} starter products into the database.")

    # 3) Test customer account.
    if Customer.get_by_email(TEST_CUSTOMER_EMAIL) is None:
        test_customer = Customer(
            full_name="Test Customer",
            email=TEST_CUSTOMER_EMAIL,
            phone="+993 61 770075",
        )
        test_customer.set_password(TEST_CUSTOMER_PASSWORD)
        db.session.add(test_customer)
        db.session.commit()
        print(f"[seed] Created test customer account: {TEST_CUSTOMER_EMAIL} / {TEST_CUSTOMER_PASSWORD}")
