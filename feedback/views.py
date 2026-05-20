from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from accounts.models import Customer
from products.models import Product
from orders.models import Order, OrderItem
from .models import Feedback


@login_required(login_url='login')
def product_feedback(request, product_id):
    """Display all feedback for a product (used in product details page)."""
    product = get_object_or_404(Product, pk=product_id)
    feedbacks = Feedback.objects.filter(product=product).select_related('customer').order_by('-created_at')
    return render(request, 'feedback/product_feedback.html', {
        'product': product,
        'feedbacks': feedbacks,
    })


@login_required(login_url='login')
def add_feedback(request, product_id):
    """Allow user to submit feedback for a product."""
    product = get_object_or_404(Product, pk=product_id)
    customer = get_object_or_404(Customer, user=request.user)

    # Check if user has already given feedback for this product
    existing_feedback = Feedback.objects.filter(
        customer=customer, product=product
    ).first()
    if existing_feedback:
        messages.info(request, f"You've already reviewed this product on {existing_feedback.created_at.strftime('%d %b %Y')}.")
        return redirect('product_detail', product_id=product_id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comments = request.POST.get('comments', '').strip()

        if not rating:
            messages.error(request, "Please select a rating.")
            return redirect('add_feedback', product_id=product_id)

        Feedback.objects.create(
            customer=customer,
            product=product,
            rating=int(rating),
            comments=comments,
            created_at=timezone.now(),
        )
        messages.success(request, "Thank you for your feedback!")
        return redirect('product_detail', product_id=product_id)

    return render(request, 'feedback/add_feedback.html', {
        'product': product,
    })


@login_required(login_url='login')
def order_feedback(request, order_id):
    """Show feedback options for products in a delivered order."""
    customer = get_object_or_404(Customer, user=request.user)
    order = get_object_or_404(Order, pk=order_id, customer=customer)

    # Only allow feedback for delivered orders
    delivery = order.delivery_set.first()
    if not delivery or delivery.delivery_status != 'delivered':
        messages.warning(request, "You can only give feedback after the product is delivered.")
        return redirect('order_confirmation', order_id=order_id)

    # Get items that haven't been reviewed yet
    items = order.items.select_related('product').all()
    feedbacks = Feedback.objects.filter(
        customer=customer,
        product__in=[item.product for item in items]
    ).values_list('product_id', flat=True)

    unreviewed_items = [item for item in items if item.product.product_id not in feedbacks]

    return render(request, 'feedback/order_feedback.html', {
        'order': order,
        'items': items,
        'unreviewed_items': unreviewed_items,
    })

