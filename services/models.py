from django.db import models
from django.utils import timezone
from accounts.models import Customer
from products.models import Product, Color
from staff.models import Staff


class Service(models.Model):
    service_id = models.AutoField(primary_key=True)
    service_name = models.CharField(unique=True, max_length=50)
    price_per_sq = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "services"
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return self.service_name


class Booking(models.Model):
    BOOKING_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("rescheduled", "Rescheduled"),
    ]

    booking_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        db_column="customer_id",
        on_delete=models.PROTECT,
    )
    service = models.ForeignKey(
        Service,
        db_column="service_id",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    product = models.ForeignKey(
        Product,
        db_column="product_id",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    color = models.ForeignKey(
        Color,
        db_column="color_id",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    area_sqft = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    required_qty = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estimated_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    service_date = models.DateField()
    booked_at = models.DateTimeField(default=timezone.now)
    address = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=BOOKING_STATUS_CHOICES,
        default="pending",
    )
    staff = models.ForeignKey(
        Staff,
        db_column="staff_id",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        managed = False
        db_table = "bookings"
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self):
        return f"Booking #{self.booking_id} - {self.status}"