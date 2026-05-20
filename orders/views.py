import hmac
import hashlib
import razorpay
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone

from products.models import Product, Color, Offer, ProductVariant
from accounts.models import Customer
from orders.models import Order, OrderItem, Payment, Delivery, Invoice
from cart.models import Cart, CartItem
from feedback.models import Feedback
from django.utils.timezone import localdate

from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO

from .email_utils import send_order_confirmation_email, send_new_order_notification_to_admin

# ── Razorpay client ────────────────────────────────────────────────
rz_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


def get_customer(user):
    try:
        return Customer.objects.get(user=user)
    except Customer.DoesNotExist:
        return None


def _build_items(customer, buy_now_data):
    """Return (items_list, total, cart_or_None)."""
    if buy_now_data:
        product    = get_object_or_404(Product, pk=buy_now_data['product_id'])
        color      = Color.objects.filter(pk=buy_now_data['color_id']).first() \
                     if buy_now_data['color_id'] else None
        variant    = ProductVariant.objects.filter(pk=buy_now_data.get('variant_id')).first()
        unit_price = variant.price if variant else product.price
        return [{'product': product, 'variant': variant, 'color': color,
                 'quantity': 1, 'subtotal': unit_price}], unit_price, None

    cart = Cart.objects.filter(customer=customer).first()
    if not cart or not cart.items.exists():
        return [], Decimal('0.00'), cart

    cart_items = cart.items.select_related('product', 'variant', 'color').all()
    items = [{'product': i.product, 'variant': i.variant, 'color': i.color,
              'quantity': i.quantity, 'subtotal': i.subtotal}
             for i in cart_items]
    total = sum((i['subtotal'] for i in items), Decimal('0.00'))
    return items, total, cart


def _create_db_order(customer, items, subtotal, payment_method, delivery_address=None,
                     offer=None, discount_amount=None,
                     razorpay_order_id=None, razorpay_payment_id=None,
                     payment_status='pending'):
    """Create Order, OrderItems, Payment and a pending Delivery row."""
    from decimal import Decimal
    discount_amount = discount_amount or Decimal('0.00')
    total = subtotal - discount_amount

    order = Order.objects.create(
        customer=customer,
        offer=offer,
        discount_amount=discount_amount,
        total_amount=total,
    )

    for item in items:
        variant    = item.get('variant')
        unit_price = variant.price if variant else item['product'].price
        OrderItem.objects.create(
            order=order, product=item['product'], variant=variant,
            color=item['color'], quantity=item['quantity'], price=unit_price,
        )
        # Reduce stock from variant if exists, else from product
        if variant:
            variant.stock_qty = max(0, variant.stock_qty - item['quantity'])
            variant.save()
        else:
            p = item['product']
            p.stock_qty = max(0, p.stock_qty - item['quantity'])
            p.save()

    payment_obj = Payment.objects.create(
        order=order, amount=total, payment_method=payment_method,
        status=payment_status,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
    )
    Invoice.objects.create(
    order          = order,
    payment        = payment_obj,
    invoice_number = f"INV-{order.order_id:05d}",
    invoice_date   = timezone.now(),
    total_amount   = total,
    )
    # Auto-create a pending Delivery row so admin can assign & track it
    Delivery.objects.create(order=order, delivery_status='pending', delivery_address=delivery_address)

    # Send email notifications
    try:
        # Send order confirmation to customer
        send_order_confirmation_email(order, customer)
        # Send new order notification to admin
        send_new_order_notification_to_admin(order, customer)
    except Exception as e:
        # Log error but don't fail order creation
        print(f"Email notification error: {e}")

    return order


def _get_valid_offers(subtotal):
    """Return active offers whose validity window covers today and min amount is met."""
    today = localdate()
    return Offer.objects.filter(
        is_active=True,
        valid_from__lte=today,
        valid_to__gte=today,
        min_order_amount__lte=subtotal,
    )


def _resolve_offer(offer_id, subtotal):
    """Return (offer, discount_amount) or (None, 0) with an error string."""
    if not offer_id:
        return None, Decimal('0.00'), None
    today = localdate()
    try:
        offer = Offer.objects.get(pk=offer_id, is_active=True,
                                  valid_from__lte=today, valid_to__gte=today)
    except Offer.DoesNotExist:
        return None, Decimal('0.00'), "Selected offer is no longer valid."
    if subtotal < offer.min_order_amount:
        return None, Decimal('0.00'), (
            f"This offer requires a minimum order of ₹{offer.min_order_amount}."
        )
    discount = (subtotal * offer.discount_percent / 100).quantize(Decimal('0.01'))
    return offer, discount, None


# ════════════════════════════════════════════════════════════════════
# BUY NOW
# ════════════════════════════════════════════════════════════════════
@login_required(login_url='login')
def buy_now(request, product_id):
    if request.method != 'POST':
        return redirect('product_detail', product_id=product_id)
    color_id   = request.POST.get('color_id') or None
    variant_id = request.POST.get('variant_id') or None
    request.session['buy_now'] = {
        'product_id': product_id,
        'color_id':   color_id,
        'variant_id': variant_id,
        'quantity':   1,
    }
    return redirect('checkout')


# ════════════════════════════════════════════════════════════════════
# CHECKOUT
# ════════════════════════════════════════════════════════════════════
@login_required(login_url='login')
def checkout(request):
    customer = get_customer(request.user)
    if not customer:
        messages.error(request, "Customer profile not found.")
        return redirect('home')

    buy_now_data = request.session.get('buy_now')
    items, subtotal, cart = _build_items(customer, buy_now_data)

    if not items:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')

    # POST → Cash on Delivery
    if request.method == 'POST':
        offer_id = request.POST.get('offer_id') or None
        offer, discount_amount, err = _resolve_offer(offer_id, subtotal)
        if err:
            messages.error(request, err)
            return redirect('checkout')
        delivery_address = request.POST.get('address', '').strip() or customer.address
        order = _create_db_order(
            customer, items, subtotal,
            payment_method='cod',
            delivery_address=delivery_address,
            offer=offer,
            discount_amount=discount_amount,
            payment_status='pending',
        )
        if buy_now_data:
            del request.session['buy_now']
        elif cart:
            cart.items.all().delete()
        messages.success(request, f"Order #{order.order_id} placed!")
        return redirect('order_confirmation', order_id=order.order_id)

    # GET → build offer list and Razorpay order for UPI/Card option
    available_offers = _get_valid_offers(subtotal)
    amount_paise      = int(subtotal * 100)
    razorpay_order_id = None
    try:
        rz_order = rz_client.order.create({
            'amount': amount_paise, 'currency': 'INR', 'payment_capture': 1
        })
        razorpay_order_id = rz_order['id']
    except Exception as e:
        print(f"Razorpay error: {e}")
        messages.warning(request, "Online payment temporarily unavailable. Please use Cash on Delivery.")

    return render(request, 'orders/checkout.html', {
        'items':             items,
        'subtotal':          subtotal,
        'customer':          customer,
        'is_buy_now':        bool(buy_now_data),
        'available_offers':  available_offers,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_key_id':   settings.RAZORPAY_KEY_ID,
        'amount_paise':      amount_paise,
    })


# ════════════════════════════════════════════════════════════════════
# PAYMENT VERIFY — Razorpay callback
# ════════════════════════════════════════════════════════════════════
@login_required(login_url='login')
def payment_verify(request):
    if request.method != 'POST':
        return redirect('home')

    customer = get_customer(request.user)
    if not customer:
        messages.error(request, "Customer profile not found.")
        return redirect('home')

    rz_payment_id  = request.POST.get('razorpay_payment_id', '')
    rz_order_id    = request.POST.get('razorpay_order_id', '')
    rz_signature   = request.POST.get('razorpay_signature', '')

    body     = f"{rz_order_id}|{rz_payment_id}".encode()
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, rz_signature):
        messages.error(request, "Payment verification failed. Please contact support.")
        return redirect('checkout')

    buy_now_data = request.session.get('buy_now')
    items, subtotal, cart = _build_items(customer, buy_now_data)

    if not items:
        messages.error(request, "Could not retrieve order items after payment.")
        return redirect('home')

    offer_id = request.POST.get('offer_id') or None
    offer, discount_amount, err = _resolve_offer(offer_id, subtotal)

    delivery_address = request.POST.get('address', '').strip()
    order = _create_db_order(
        customer, items, subtotal,
        payment_method      = 'upi',
        delivery_address    = delivery_address,
        offer               = offer,
        discount_amount     = discount_amount,
        razorpay_order_id   = rz_order_id,
        razorpay_payment_id = rz_payment_id,
        payment_status      = 'paid',
    )

    if buy_now_data:
        del request.session['buy_now']
    elif cart:
        cart.items.all().delete()

    messages.success(request, f"Payment successful! Order #{order.order_id} confirmed.")
    return redirect('order_confirmation', order_id=order.order_id)


# ════════════════════════════════════════════════════════════════════
# ORDER CONFIRMATION
# ════════════════════════════════════════════════════════════════════
@login_required(login_url='login')
def order_confirmation(request, order_id):
    customer = get_customer(request.user)
    order    = get_object_or_404(Order, pk=order_id, customer=customer)
    items    = OrderItem.objects.filter(order=order).select_related('product', 'color')
    payment  = Payment.objects.filter(order=order).first()
    delivery = Delivery.objects.filter(order=order).first()

    # Check which items can be reviewed (delivered and not yet reviewed)
    can_review = []
    if delivery and delivery.delivery_status == 'delivered':
        feedbacks = Feedback.objects.filter(
            customer=customer,
            product__in=[item.product for item in items]
        ).values_list('product_id', flat=True)
        can_review = [item for item in items if item.product.product_id not in feedbacks]

    return render(request, 'orders/order_confirmation.html', {
        'order': order, 'items': items, 'payment': payment,
        'delivery': delivery, 'can_review': can_review,
    })


# ════════════════════════════════════════════════════════════════════
# MY ORDERS
# ════════════════════════════════════════════════════════════════════
@login_required(login_url='login')
def my_orders(request):
    customer = get_customer(request.user)
    if not customer:
        messages.error(request, "Customer profile not found.")
        return redirect('home')
    orders     = Order.objects.filter(customer=customer).order_by('-order_date')
    order_data = []
    for order in orders:
        items    = OrderItem.objects.filter(order=order).select_related('product', 'color')
        payment  = Payment.objects.filter(order=order).first()
        delivery = Delivery.objects.filter(order=order).first()

        # Check if order is delivered and count unreviewed items
        can_review_count = 0
        if delivery and delivery.delivery_status == 'delivered':
            feedbacks = Feedback.objects.filter(
                customer=customer,
                product__in=[item.product for item in items]
            ).values_list('product_id', flat=True)
            can_review_count = sum(1 for item in items if item.product.product_id not in feedbacks)

        order_data.append({
            'order': order, 'items': items,
            'payment': payment, 'delivery': delivery,
            'can_review_count': can_review_count,
        })
    return render(request, 'orders/my_orders.html', {'order_data': order_data})


@login_required(login_url='login')
def download_invoice(request, order_id):
    customer = get_customer(request.user)
    order    = get_object_or_404(Order, pk=order_id, customer=customer)
    invoice  = get_object_or_404(Invoice, order=order)
    items    = OrderItem.objects.filter(order=order).select_related('product', 'color')
    payment  = Payment.objects.filter(order=order).first()

    html_string = render_to_string('orders/invoice_pdf.html', {
        'order':    order,
        'invoice':  invoice,
        'items':    items,
        'payment':  payment,
        'customer': customer,
    })

    buffer = BytesIO()
    pisa.CreatePDF(html_string, dest=buffer)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice-{invoice.invoice_number}.pdf"'
    return response