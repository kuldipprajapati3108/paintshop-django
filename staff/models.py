from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Staff(models.Model):
    STAFF_STATUS_CHOICES = [
        ("available", "Available"),
        ("working", "Working"),
        ("on_leave", "On Leave"),
    ]

    ROLE_CHOICES = [                       
        ("delivery", "Delivery"),
        ("painter", "Painter"),
        ("manager", "Manager"),
    ]

    staff_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES)
    phone = models.CharField(unique=True, max_length=15)
    email = models.EmailField(unique=True, max_length=150)
    availability_status = models.CharField(
        max_length=15, choices=STAFF_STATUS_CHOICES, default="available"
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "staff"
        verbose_name = "Staff Member"
        verbose_name_plural = "Staff Members"

    def __str__(self):
        return f"{self.full_name} - {self.role}"