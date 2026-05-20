from django.shortcuts import render, get_object_or_404
from .models import Category, Brand, Product, ProductImage, ProductColor
from feedback.models import Feedback
from services.models import Service


def home(request):
    from .models import Brand
    brands = Brand.objects.all()
    featured_products = Product.objects.select_related('category', 'brand').all()[:8]
    services = Service.objects.all()[:4]

    return render(request, "home.html", {
        "brands": brands,
        "products": featured_products,
        "services": services,
    })


def product_list(request):
    products = Product.objects.select_related('category', 'brand').all()

    # --- Filters from GET params ---
    category_id = request.GET.get('category')
    brand_id    = request.GET.get('brand')
    min_price   = request.GET.get('min_price')
    max_price   = request.GET.get('max_price')
    in_stock    = request.GET.get('in_stock')

    if category_id:
        products = products.filter(category__category_id=category_id)
    if brand_id:
        products = products.filter(brand__brand_id=brand_id)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if in_stock:
        products = products.filter(stock_qty__gt=0)

    categories = Category.objects.all()
    brands     = Brand.objects.all()
    services   = Service.objects.all()[:4]

    return render(request, "products/product_list.html", {
        "products":    products,
        "categories":  categories,
        "brands":      brands,
        "services":    services,
        # pass active filters back so sidebar can show them checked
        "active_category": category_id,
        "active_brand":    brand_id,
        "min_price":       min_price or '',
        "max_price":       max_price or '',
        "in_stock":        in_stock,
    })


def product_detail(request, product_id):
    from .models import ProductVariant
    product          = get_object_or_404(Product.objects.select_related('category', 'brand'), pk=product_id)
    images           = ProductImage.objects.filter(product=product)
    featured_products = Product.objects.select_related('category', 'brand').exclude(pk=product_id)[:4]
    services         = Service.objects.all()[:4]
    product_colors   = ProductColor.objects.filter(product=product).select_related('color')
    variants         = ProductVariant.objects.filter(product=product).order_by('price')
    feedbacks        = Feedback.objects.filter(product=product).select_related('customer').order_by('-created_at')[:10]

    # Check if current user has already reviewed this product
    user_has_reviewed = False
    if request.user.is_authenticated:
        from accounts.models import Customer
        try:
            customer = Customer.objects.get(user=request.user)
            user_has_reviewed = Feedback.objects.filter(
                customer=customer, product=product
            ).exists()
        except Customer.DoesNotExist:
            pass

    return render(request, "products/product_details.html", {
        "product":          product,
        "images":           images,
        "products":         featured_products,
        "services":         services,
        "product_colors":   product_colors,
        "variants":         variants,
        "feedbacks":        feedbacks,
        "user_has_reviewed": user_has_reviewed,
    })


def colour_catalogue(request):
    from .models import Color
    from itertools import groupby
 
    colors = Color.objects.all().order_by('family', 'color_name')
 
    # Group by family
    families = {}
    for color in colors:
        fam = color.family or 'Other'
        if fam not in families:
            families[fam] = []
        families[fam].append(color)
 
    # Preserve a nice display order
    family_order = ['Whites', 'Neutrals', 'Blues', 'Greens', 'Yellows',
                    'Oranges', 'Reds', 'Pinks', 'Purples', 'Browns', 'Other']
    ordered_families = {k: families[k] for k in family_order if k in families}
    # append any remaining families not in the order list
    for k in families:
        if k not in ordered_families:
            ordered_families[k] = families[k]
 
    return render(request, 'products/colour_catalogue.html', {
        'families':     ordered_families,
        'all_families': list(ordered_families.keys()),
    })