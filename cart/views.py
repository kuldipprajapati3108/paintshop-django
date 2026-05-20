from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal

from products.models import Product, Color, ProductVariant
from accounts.models import Customer
from .models import Cart, CartItem


def get_customer(user):
    try:
        return Customer.objects.get(user=user)
    except Customer.DoesNotExist:
        return None


# ── Add to cart ────────────────────────────────────────────────────
@login_required(login_url='login')
def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('product_detail', product_id=product_id)

    customer = get_customer(request.user)
    if not customer:
        messages.error(request, "Customer profile not found.")
        return redirect('product_detail', product_id=product_id)

    product    = get_object_or_404(Product, pk=product_id)
    color_id   = request.POST.get('color_id') or None
    variant_id = request.POST.get('variant_id') or None
    color      = Color.objects.filter(pk=color_id).first() if color_id else None
    variant    = ProductVariant.objects.filter(pk=variant_id).first() if variant_id else None

    # Use variant stock limit if a variant was selected
    stock_limit = variant.stock_qty if variant else product.stock_qty

    cart, _ = Cart.objects.get_or_create(customer=customer)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, color=color, variant=variant,
        defaults={'quantity': 1}
    )
    if not created:
        if cart_item.quantity < stock_limit:
            cart_item.quantity += 1
            cart_item.save()

    messages.success(request, f'"{product.product_name}" added to cart!')
    return redirect('cart')


# ── Cart page ──────────────────────────────────────────────────────
@login_required(login_url='login')
def cart_view(request):
    customer = get_customer(request.user)
    if not customer:
        messages.error(request, "Customer profile not found.")
        return redirect('home')

    cart  = Cart.objects.filter(customer=customer).first()
    items = cart.items.select_related('product', 'color', 'variant').all() if cart else []
    total = sum(item.subtotal for item in items) if items else Decimal('0.00')

    return render(request, 'cart/cart.html', {
        'cart':  cart,
        'items': items,
        'total': total,
    })


# ── Update / remove cart item ──────────────────────────────────────
@login_required(login_url='login')
def update_cart(request, item_id):
    if request.method != 'POST':
        return redirect('cart')

    cart_item = get_object_or_404(CartItem, pk=item_id)
    customer  = get_customer(request.user)
    if cart_item.cart.customer != customer:
        return redirect('cart')

    # Respect variant stock limit when increasing
    stock_limit = (
        cart_item.variant.stock_qty if cart_item.variant
        else cart_item.product.stock_qty
    )

    action = request.POST.get('action')
    if action == 'increase':
        if cart_item.quantity < stock_limit:
            cart_item.quantity += 1
            cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    elif action == 'remove':
        cart_item.delete()

    return redirect('cart')