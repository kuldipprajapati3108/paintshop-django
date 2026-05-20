from django.db import models
from django.utils import timezone
from accounts.models import Customer
from products.models import Product, Color, ProductVariant


class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    customer = models.OneToOneField(
        Customer,
        db_column='customer_id',
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'cart'
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        return f"Cart of {self.customer}"

    def get_total(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(
        Cart,
        db_column='cart_id',
        on_delete=models.CASCADE,
        related_name='items',
    )
    product = models.ForeignKey(
        Product,
        db_column='product_id',
        on_delete=models.CASCADE,
    )
    variant = models.ForeignKey(
        ProductVariant, 
        db_column='variant_id', 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    color = models.ForeignKey(
        Color,
        db_column='color_id',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'cart_items'
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return f"{self.quantity} x {self.product}"

    @property
    def subtotal(self):
        unit_price = self.variant.price if self.variant else self.product.price
        return unit_price * self.quantity