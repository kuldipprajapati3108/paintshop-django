"""
Email utilities for order and delivery notifications.
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from .models import Payment


def send_email_notification(
    subject, template_name, context, recipient_list, from_email=None, reply_to=None
):
    """
    Generic function to send email with HTML template.

    Args:
        subject: Email subject
        template_name: Path to HTML template (without .html extension)
        context: Dictionary with template context
        recipient_list: List of recipient email addresses
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
        reply_to: Reply-to email address
    """
    try:
        from_email = from_email or settings.DEFAULT_FROM_EMAIL

        # Render HTML content
        html_content = render_to_string(template_name, context)

        # Create plain text version
        text_content = strip_tags(html_content)

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list,
            reply_to=[reply_to] if reply_to else None,
        )
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send(fail_silently=False)

        return True
    except Exception as e:
        # Log error in production
        print(f"Email sending failed: {str(e)}")
        return False


def send_order_confirmation_email(order, customer):
    """
    Send order confirmation email to customer.

    Args:
        order: Order instance
        customer: Customer instance
    """
    items = order.items.select_related("product", "color").all()
    payment = Payment.objects.filter(order=order).first()

    context = {
        "order": order,
        "customer": customer,
        "items": items,
        "payment": payment,
        "total": order.total_amount,
        "site_name": "Shree Shankar Traders",
    }

    subject = f"Order Confirmation - Order #{order.order_id} - Shree Shankar Traders"
    template_name = "emails/order_confirmation.html"

    return send_email_notification(
        subject=subject,
        template_name=template_name,
        context=context,
        recipient_list=[customer.email],
    )


def send_order_status_update_email(order, customer):
    """
    Send order status update email to customer.

    Args:
        order: Order instance (with updated status)
        customer: Customer instance
    """
    context = {
        "order": order,
        "customer": customer,
        "status": order.get_status_display(),
        "site_name": "Shree Shankar Traders",
    }

    subject = f"Order Status Update - Order #{order.order_id} - Shree Shankar Traders"
    template_name = "emails/order_status_update.html"

    return send_email_notification(
        subject=subject,
        template_name=template_name,
        context=context,
        recipient_list=[customer.email],
    )


def send_delivery_update_email(delivery, order, customer):
    """
    Send delivery status update email to customer.

    Args:
        delivery: Delivery instance (with updated status)
        order: Order instance
        customer: Customer instance
    """
    items = order.items.select_related("product", "color").all()

    context = {
        "delivery": delivery,
        "order": order,
        "customer": customer,
        "items": items,
        "total": order.total_amount,
        "status": delivery.get_delivery_status_display(),
        "staff": delivery.staff,
        "site_name": "Shree Shankar Traders",
    }

    subject = f"Delivery Update - Order #{order.order_id} - Shree Shankar Traders"
    template_name = "emails/delivery_update.html"

    return send_email_notification(
        subject=subject,
        template_name=template_name,
        context=context,
        recipient_list=[customer.email],
    )


def send_new_order_notification_to_admin(order, customer):
    """
    Send new order notification to admin defined in settings.ADMIN_EMAIL.

    Args:
        order: Order instance
        customer: Customer instance
    """
    admin_email = getattr(settings, "ADMIN_EMAIL", None)
    if not admin_email:
        return False

    items = order.items.select_related("product", "color").all()

    context = {
        "order": order,
        "customer": customer,
        "items": items,
        "total": order.total_amount,
        "site_name": "Shree Shankar Traders",
    }

    subject = f"[ALERT] New Order #{order.order_id} Received - Shree Shankar Traders"
    template_name = "emails/admin_new_order.html"

    return send_email_notification(
        subject=subject,
        template_name=template_name,
        context=context,
        recipient_list=[admin_email],
    )


def send_low_stock_alert(order, low_stock_products, threshold=10):
    """
    Send low stock alert to admin when product stock falls below threshold.

    Args:
        order: Order instance that triggered the alert
        low_stock_products: Queryset or list of Product instances with stock < threshold
        threshold: The stock threshold (default 10)
    """
    admin_email = getattr(settings, "ADMIN_EMAIL", None)
    if not admin_email or not low_stock_products:
        return False

    from django.utils import timezone

    context = {
        "order": order,
        "low_stock_products": low_stock_products,
        "threshold": threshold,
        "alert_time": timezone.now(),
        "site_name": "Shree Shankar Traders",
    }

    subject = f"[STOCK ALERT] Low Stock Products - Order #{order.order_id} - Shree Shankar Traders"
    template_name = "emails/low_stock_alert.html"

    return send_email_notification(
        subject=subject,
        template_name=template_name,
        context=context,
        recipient_list=[admin_email],
    )