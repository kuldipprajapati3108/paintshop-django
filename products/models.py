from django.db import models
from django.utils import timezone


class Brand(models.Model):
    brand_id   = models.AutoField(primary_key=True)
    brand_name = models.CharField(max_length=50, unique=True)
    logo       = models.ImageField(upload_to="brands/", blank=True, null=True)

    class Meta:
        managed = False
        db_table = "brands"
        verbose_name = "Brand"
        verbose_name_plural = "Brands"

    def __str__(self):
        return self.brand_name


class Category(models.Model):
    category_id   = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=50, unique=True)

    class Meta:
        managed = False
        db_table = "categories"
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.category_name


class Color(models.Model):
    FAMILY_CHOICES = [
        ('Whites',   'Whites'),
        ('Blues',    'Blues'),
        ('Greens',   'Greens'),
        ('Yellows',  'Yellows'),
        ('Pinks',    'Pinks'),
        ('Reds',     'Reds'),
        ('Purples',  'Purples'),
        ('Neutrals', 'Neutrals'),
        ('Browns',   'Browns'),
        ('Oranges',  'Oranges'),
    ]

    color_id   = models.AutoField(primary_key=True)
    shade_code = models.CharField(max_length=20, blank=True, null=True)
    family     = models.CharField(max_length=50, blank=True, null=True, choices=FAMILY_CHOICES)
    color_code = models.CharField(max_length=20)
    color_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = "colors"
        verbose_name = "Color"
        verbose_name_plural = "Colors"

    def __str__(self):
        return self.color_name


class Product(models.Model):
    product_id   = models.AutoField(primary_key=True)
    category     = models.ForeignKey(Category, db_column="category_id", on_delete=models.SET_NULL, null=True, blank=True)
    brand        = models.ForeignKey(Brand, db_column="brand_id", on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=100)
    description  = models.TextField(blank=True, null=True)
    # Base price shown on product listing — each variant may override this
    price        = models.DecimalField(max_digits=10, decimal_places=2)
    # Base stock — used when product has no variants
    stock_qty    = models.PositiveIntegerField()
    expiry_date  = models.DateField(blank=True, null=True)
    created_at   = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "products"
        verbose_name = "Product"
        verbose_name_plural = "Products"

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        return img.image_url if img else None

    def __str__(self):
        return self.product_name


class ProductVariant(models.Model):
    WEIGHT_UNIT_CHOICES = [
        ('ml',    'Millilitres (ml)'),
        ('litre', 'Litres (L)'),
        ('kg',    'Kilograms (kg)'),
        ('gram',  'Grams (g)'),
    ]
    SIZE_UNIT_CHOICES = [
        ('inch', 'Inch'),
        ('cm',   'Centimetre (cm)'),
        ('mm',   'Millimetre (mm)'),
    ]

    variant_id   = models.AutoField(primary_key=True)
    product      = models.ForeignKey(Product, db_column='product_id', on_delete=models.CASCADE, related_name='variants')
    # Human-readable label shown to customers — e.g. "1 Litre", "4 Inch"
    label        = models.CharField(max_length=50)
    weight_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    weight_unit  = models.CharField(max_length=10, choices=WEIGHT_UNIT_CHOICES, blank=True, null=True)
    size_value   = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    size_unit    = models.CharField(max_length=10, choices=SIZE_UNIT_CHOICES, blank=True, null=True)
    price        = models.DecimalField(max_digits=10, decimal_places=2)
    stock_qty    = models.PositiveIntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'product_variants'
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'

    def __str__(self):
        return f"{self.product.product_name} — {self.label}"

    @property
    def display_spec(self):
        parts = []
        if self.weight_value and self.weight_unit:
            parts.append(f"{self.weight_value} {self.weight_unit}")
        if self.size_value and self.size_unit:
            parts.append(f"{self.size_value} {self.size_unit}")
        return " / ".join(parts) if parts else self.label


class ProductImage(models.Model):
    image_id   = models.AutoField(primary_key=True)
    product    = models.ForeignKey(Product, db_column="product_id", on_delete=models.CASCADE, related_name="images")
    image_url  = models.ImageField(upload_to="products/")
    alt_text   = models.CharField(max_length=50)
    is_primary = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = "product_images"
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return self.alt_text


class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='colors')
    color   = models.ForeignKey('Color', on_delete=models.CASCADE)

    class Meta:
        db_table = 'product_colors'
        unique_together = ('product', 'color')

    def __str__(self):
        return f"{self.product.product_name} — {self.color.color_name}"


class Offer(models.Model):
    offer_id         = models.AutoField(primary_key=True)
    offer_name       = models.CharField(max_length=50)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valid_from       = models.DateField()
    valid_to         = models.DateField()
    is_active        = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "offers"
        verbose_name = "Offer"
        verbose_name_plural = "Offers"

    def __str__(self):
        return self.offer_name