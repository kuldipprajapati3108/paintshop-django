from products.models import Brand, Category, Color, Product, ProductImage, Offer, ProductColor, ProductVariant
from orders.models import Order, OrderItem, Payment, Delivery, Invoice
from services.models import Booking, Service
from cart.models import Cart, CartItem
from accounts.models import Customer
from django.contrib.auth.models import User
from feedback.models import Feedback
from staff.models import Staff


ADMIN_MODULES = {
    # ── FULL CRUD ──────────────────────────────────────────────────────────────
    "users": {
        "model": User,
        "title": "User",
        "list_display": [
            "id",
            "username",
            "password",
            "is_superuser",
            "is_staff",
            "date_joined",
        ],
        
        "exclude_fields": [
            "first_name",
            "last_name",
            "last_login",
            "is_active",
            "email",
            "groups",
            "user_permissions",
        ],
        "allow_add": True,
        "allow_edit": True,
        "allow_delete": True,
    },
    "staff": {
        "model": Staff,
        "title": "Staff",
        "readonly_fields": ["created_at"],
        "allow_add": True,
        "allow_edit": True,
        "allow_delete": True,
    },
    "products": {
        "model": Product,
        "title": "Products",
        "readonly_fields": ["created_at"],
        "allow_add": True,
        "allow_edit": True,
        "allow_delete": True,
        # "inlines": [
        #     {
        #         "model": ProductImage,
        #         "fk_name": "product",
        #         "fields": ["image_url", "alt_text", "is_primary"],
        #         "extra": 2,
        #         "title": "Product Images",
        #     }
        # ],
    },
    "product_image": {
        "model": ProductImage,
        "title": "Product Images",
        "allow_add": True,
        "allow_edit": True,
        "allow_delete": True,
        "hidden": True,
    },
    "product_colors": {
        "model": ProductColor,
        "title": "Product Colors",
        "allow_add": True,
        "allow_edit": True,
        "allow_delete": True,
        "hidden": True,
    },
    "product_variants": {
        "model": ProductVariant,
        "title": "Product Variants",
        "allow_add": True,
        "allow_edit": True,
        "allow_delete": True,
    },
    "categories": {
        "model": Category,
        "title": "Categories",
        "allow_add": True,
        "allow_edit": True,
        "allow_delete": True,
    },
    "colors": {
        "model": Color,
        "title": "Colors",
        "allow_add": True,
        "allow_edit": True,
        "allow_delete": True,
    },
    "offers": {
        "model": Offer,
        "title": "Offers",
        "allow_add": True,
        "allow_edit": True,
        "allow_delete": True,
    },
    "services": {
        "model": Service,
        "title": "Services",
        "allow_add": True,
        "allow_edit": True,
        "allow_delete": True,
    },
    "brands": {
        "model": Brand,
        "title": "Brands",
        "allow_add": True,
        "allow_edit": True,
        "allow_delete": True,
    },
    # ── EDIT STATUS / ASSIGN ONLY (no add, no delete) ─────────────────────────

    "orders": {
        "model": Order,
        "title": "Orders",
        "readonly_fields": ["customer", "order_date", "offer", "discount_amount"],
        "allow_add": False,
        "allow_edit": True,
        "allow_delete": False,
    },
    "bookings": {
        "model": Booking,
        "title": "Bookings",
        "readonly_fields": [
            "customer", "service", "product", "color",
            "area_sqft", "required_qty", "estimated_price",
            "service_date", "booked_at", "address",
        ],
        "allow_add": False,
        "allow_edit": True,
        "allow_delete": False,
    },
    "deliveries": {
        "model": Delivery,
        "title": "Deliveries",
        "readonly_fields": ["order", "delivery_date", "delivery_address"],
        "allow_add": False,
        "allow_edit": True,
        "allow_delete": False,
    },

    # ── VIEW ONLY (no add, no edit, no delete) ─────────────────────────────────

    "customers": {
        "model": Customer,
        "title": "Customers",
        "readonly_fields": ["user", "cust_name", "email", "phone", "address"],
        "allow_add": False,
        "allow_edit": False,
        "allow_delete": False,
    },
    "payments": {
        "model": Payment,
        "title": "Payments",
        "readonly_fields": [
            "order", "booking", "amount",
            "payment_method", "payment_date", "status",
        ],
        "allow_add": False,
        "allow_edit": False,
        "allow_delete": False,
    },
    "invoices": {
        "model": Invoice,
        "title": "Invoices",
        "readonly_fields": [
            "order", "payment", "invoice_number",
            "invoice_date", "total_amount",
        ],
        "allow_add": False,
        "allow_edit": False,
        "allow_delete": False,
    },

    # ── DELETE ONLY (can remove spam, cannot add or edit) ──────────────────────

    "feedbacks": {
        "model": Feedback,
        "title": "Feedbacks",
        "readonly_fields": [
            "customer", "product", "service",
            "rating", "comments", "created_at",
        ],
        "allow_add": False,
        "allow_edit": False,
        "allow_delete": True,
    },
}