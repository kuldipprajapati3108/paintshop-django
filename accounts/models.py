from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    cust_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=150, unique=True)
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "customers"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"{self.cust_name} (Customer #{self.customer_id})"