from django.db import models
from django.utils import timezone
from products.models import Product, Color, ProductVariant
from accounts.models import Customer
from services.models import Booking
from staff.models import Staff


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    order_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer, db_column="customer_id", on_delete=models.PROTECT
    )
    order_date = models.DateTimeField(default=timezone.now)
    offer = models.ForeignKey(
        "products.Offer",
        db_column="offer_id",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=15, choices=ORDER_STATUS_CHOICES, default="pending"
    )

    class Meta:
        managed = False
        db_table = "orders"
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{self.order_id}"


class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        Order, db_column="order_id", on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        Product, db_column="product_id", on_delete=models.PROTECT
    )
    variant       = models.ForeignKey(
        ProductVariant, db_column="variant_id", on_delete=models.SET_NULL, blank=True, null=True)
    color = models.ForeignKey(
        Color, db_column="color_id", on_delete=models.SET_NULL, blank=True, null=True
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = "order_items"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"Item #{self.order_item_id} - {self.product}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("upi", "UPI"),
        ("cod", "Cash on Delivery"),
    ]

    payment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        Order, db_column="order_id", on_delete=models.PROTECT, blank=True, null=True
    )
    booking = models.ForeignKey(
        Booking,
        db_column="booking_id",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=15, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    payment_date = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "payments"

    def __str__(self):
        return f"Payment #{self.payment_id}"


class Delivery(models.Model):
    DELIVERY_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("assigned", "Assigned"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
    ]

    delivery_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        db_column="order_id",
        on_delete=models.CASCADE,
    )
    staff = models.ForeignKey(
        Staff, db_column="staff_id", on_delete=models.SET_NULL, blank=True, null=True
    )
    delivery_status = models.CharField(
        max_length=20, choices=DELIVERY_STATUS_CHOICES, default="pending"
    )
    delivery_date = models.DateField(blank=True, null=True)
    delivery_address = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "deliveries"

    def __str__(self):
        return f"Delivery #{self.delivery_id}"


class Invoice(models.Model):
    invoice_id = models.AutoField(primary_key=True)
    order = models.OneToOneField(
        Order,
        db_column="order_id",
        on_delete=models.PROTECT,
    )
    payment = models.OneToOneField(
        Payment,
        db_column="payment_id",
        on_delete=models.PROTECT,
    )
    invoice_number = models.CharField(max_length=20, unique=True)
    invoice_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = "invoices"

    def __str__(self):
        return self.invoice_number
