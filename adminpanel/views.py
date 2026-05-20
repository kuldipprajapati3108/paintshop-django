from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import modelform_factory, DateInput, inlineformset_factory
from .admin_config import ADMIN_MODULES
from .utils import get_model_fields
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User


def admin_check(user):
    return user.is_superuser


from django.utils import timezone
from datetime import timedelta
from orders.models import Order, Payment, Delivery
from accounts.models import Customer
from products.models import Product
from services.models import Booking


@login_required
@user_passes_test(admin_check)
def dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    context = {
        "orders_today": Order.objects.filter(order_date__date=today).count(),
        "orders_pending": Order.objects.filter(status="pending").count(),
        "total_customers": Customer.objects.count(),
        "out_of_stock": Product.objects.filter(stock_qty=0).count(),
        "pending_bookings": Booking.objects.filter(status="pending"),
        "low_stock_products": Product.objects.filter(stock_qty__lt=10).order_by(
            "stock_qty"
        ),
        "overdue_deliveries": Delivery.objects.filter(delivery_date__lt=today).exclude(
            delivery_status="delivered"
        ),
        "pending_payments": Payment.objects.filter(status="pending").count(),
        "recent_orders": Order.objects.select_related("customer").order_by(
            "-order_date"
        )[:10],
    }

    return render(request, "adminpanel/dashboard.html", context)


@login_required
@user_passes_test(admin_check)
def general_list(request, module):
    config = ADMIN_MODULES.get(module)
    if not config:
        return redirect("admin_dashboard")

    model = config["model"]
    fields = get_model_fields(
        model, config.get("exclude_fields"), config.get("list_display")
    )

    return render(
        request,
        "adminpanel/general_list.html",
        {
            "title": config["title"],
            "objects": model.objects.all(),
            "fields": fields,
            "module": module,
            "allow_add": config["allow_add"],
            "allow_edit": config["allow_edit"],
            "allow_delete": config["allow_delete"],
        },
    )


def _date_widgets(model):
    return {
        field.name: DateInput(attrs={"type": "date"})
        for field in model._meta.get_fields()
        if hasattr(field, "get_internal_type")
        and field.get_internal_type() == "DateField"
    }


def _apply_readonly_styling(form, readonly_fields, pk):
    """
    Make readonly fields visually non-editable.
    - Text-like widgets: use HTML readonly attr so the browser STILL submits
      the value (no validation breakage).
    - Select/checkbox widgets: use disabled attr for display; the POST handler
      restores their values from the instance before validation runs.
    """
    TEXT_LIKE = (
        "TextInput",
        "EmailInput",
        "NumberInput",
        "DateInput",
        "DateTimeInput",
        "DateTimeLocalInput",
        "Textarea",
        "URLInput",
        "HiddenInput",
    )
    password_only_on_edit = ["password"]
    readonly_style = "background:#f5f6fa;cursor:not-allowed;color:#6b7280;"

    for field_name in readonly_fields:
        if field_name not in form.fields:
            continue
        if field_name in password_only_on_edit and not pk:
            continue
        field = form.fields[field_name]
        widget_name = field.widget.__class__.__name__
        if widget_name in TEXT_LIKE:
            field.widget.attrs["readonly"] = True
            field.widget.attrs["style"] = (
                field.widget.attrs.get("style", "") + readonly_style
            )
        else:
            field.disabled = True


@login_required
@user_passes_test(admin_check)
def general_form(request, module, pk=None):
    config = ADMIN_MODULES.get(module)
    if not config:
        return redirect("admin_dashboard")

    model = config["model"]
    instance = get_object_or_404(model, pk=pk) if pk else None

    Form = modelform_factory(
        model,
        exclude=config.get("exclude_fields", []),
        widgets=_date_widgets(model),
    )

    # ── Build inline formset classes ─────────────────────────────────
    inline_configs = config.get("inlines", [])
    InlineFormSets = []

    for inline in inline_configs:
        InlineFS = inlineformset_factory(
            model,
            inline["model"],
            fields=inline["fields"],
            exclude=config.get("exclude_fields", []),
            extra=inline.get("extra", 1),
            can_delete=True,
            widgets=_date_widgets(inline["model"]),
        )
        InlineFormSets.append((inline, InlineFS))

    readonly_fields = config.get("readonly_fields", [])

    # ── Handle POST ──────────────────────────────────────────────────
    if request.method == "POST":
        # Browsers do NOT submit disabled fields, so readonly values arrive
        # empty and fail required-field validation.
        # Fix: copy the POST QueryDict and restore each readonly field's
        # current value from the saved instance before passing to the form.
        post_data = request.POST.copy()

        if instance:
            password_only_on_edit = ["password"]
            for field_name in readonly_fields:
                if field_name in password_only_on_edit and not pk:
                    continue
                # FK fields are stored as <name>_id on the instance
                raw = getattr(instance, field_name + "_id", None)
                if raw is None:
                    raw = getattr(instance, field_name, None)
                if raw is not None:
                    post_data[field_name] = str(raw)

        form = Form(post_data, request.FILES, instance=instance)

        inline_formsets = [
            (inline_cfg, FS(post_data, request.FILES, instance=instance))
            for inline_cfg, FS in InlineFormSets
        ]

        form_valid = form.is_valid()
        inlines_valid = all(fs.is_valid() for _, fs in inline_formsets)

        if form_valid and inlines_valid:
            # Special handling for User model to properly hash passwords
            if model is User:
                cleaned_data = form.cleaned_data
                password = cleaned_data.get('password')

                if instance:
                    # Editing existing user
                    user = instance
                    # Only update password if a new one is provided (not the existing hash)
                    # In the form, if password field is left unchanged, it may contain the hashed value
                    # We check if it's a new plaintext password by attempting to verify it doesn't match the current hash
                    if password and password != user.password:
                        user.set_password(password)
                    # Update other fields
                    for field, value in cleaned_data.items():
                        if field != 'password':
                            setattr(user, field, value)
                    user.save()
                    saved = user
                else:
                    # Creating new user - use create_user() to hash password
                    user_data = {k: v for k, v in cleaned_data.items() if k != 'password'}
                    saved = User.objects.create_user(password=password, **user_data)
            else:
                saved = form.save()

            for _, fs in inline_formsets:
                fs.instance = saved
                fs.save()
            return redirect(reverse("admin_list", kwargs={"module": module}))

        # Re-apply styling so the error re-render looks correct
        _apply_readonly_styling(form, readonly_fields, pk)

    else:
        form = Form(instance=instance)
        inline_formsets = [
            (inline_cfg, FS(instance=instance)) for inline_cfg, FS in InlineFormSets
        ]
        _apply_readonly_styling(form, readonly_fields, pk)

    return render(
        request,
        "adminpanel/general_form.html",
        {
            "form": form,
            "title": f"{'Edit' if pk else 'Add'} {config['title']}",
            "list_url": reverse("admin_list", kwargs={"module": module}),
            "inline_formsets": inline_formsets,
        },
    )


@login_required
@user_passes_test(admin_check)
def general_delete(request, module, pk):
    config = ADMIN_MODULES.get(module)
    if not config or not config.get("allow_delete"):
        return redirect(reverse("admin_list", kwargs={"module": module}))

    model = config["model"]
    obj = get_object_or_404(model, pk=pk)

    if request.method == "POST":
        obj.delete()
        return redirect(reverse("admin_list", kwargs={"module": module}))

    return render(
        request,
        "adminpanel/confirm_delete.html",
        {
            "object": obj,
            "title": f"Delete {config['title']}",
            "list_url": reverse("admin_list", kwargs={"module": module}),
        },
    )

# ════════════════════════════════════════════════════════════════════
# DELIVERY MANAGEMENT (custom views)
# ════════════════════════════════════════════════════════════════════
from orders.models import Delivery
from staff.models import Staff
 
@login_required
@user_passes_test(admin_check)
def delivery_list(request):
    status_filter = request.GET.get('status', '')
 
    deliveries = Delivery.objects.select_related(
        'order', 'order__customer', 'staff'
    ).order_by('-order__order_date')
 
    if status_filter:
        deliveries = deliveries.filter(delivery_status=status_filter)
 
    # Count badges for each status
    from django.db.models import Count
    status_counts = {
        d['delivery_status']: d['count']
        for d in Delivery.objects.values('delivery_status').annotate(count=Count('delivery_id'))
    }
 
    return render(request, 'adminpanel/deliveries.html', {
        'deliveries':    deliveries,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'status_choices': Delivery.DELIVERY_STATUS_CHOICES,
    })
 
 
@login_required
@user_passes_test(admin_check)
def delivery_update(request, pk):
    from orders.email_utils import send_delivery_update_email, send_order_status_update_email

    delivery = get_object_or_404(
        Delivery.objects.select_related('order', 'order__customer', 'staff'), pk=pk
    )
    order      = delivery.order
    items      = order.items.select_related('product', 'color').all()
    payment    = Payment.objects.filter(order=order).first()
    total      = sum(i.price * i.quantity for i in items)
    staff_list = Staff.objects.filter(role='delivery').order_by('full_name')

    # Store original status to detect changes
    original_delivery_status = delivery.delivery_status
    original_order_status = order.status

    if request.method == 'POST':
        new_status        = request.POST.get('delivery_status')
        new_staff_id      = request.POST.get('staff_id') or None
        new_delivery_date = request.POST.get('delivery_date') or None
        new_order_status  = request.POST.get('order_status')

        delivery.delivery_status = new_status
        delivery.staff = Staff.objects.filter(pk=new_staff_id).first() if new_staff_id else None
        delivery.delivery_date   = new_delivery_date
        delivery.save()

        if new_order_status:
            order.status = new_order_status
            order.save()

        messages.success(request, f"Delivery for Order #{order.order_id} updated.")

        # Send email notifications if delivery status changed
        if original_delivery_status != new_status:
            try:
                send_delivery_update_email(delivery, order, order.customer)
            except Exception as e:
                print(f"Delivery email error: {e}")

        # Send email if order status changed
        if original_order_status != new_order_status:
            try:
                send_order_status_update_email(order, order.customer)
            except Exception as e:
                print(f"Order status email error: {e}")

        return redirect('admin_deliveries')

    return render(request, 'adminpanel/delivery_update.html', {
        'delivery':       delivery,
        'order':          order,
        'items':          items,
        'payment':        payment,
        'total':          total,
        'staff_list':     staff_list,
        'status_choices': Delivery.DELIVERY_STATUS_CHOICES,
        'order_status_choices': order.ORDER_STATUS_CHOICES,
    })


# ════════════════════════════════════════════════════════════════════
# REPORTS
# ════════════════════════════════════════════════════════════════════

@login_required
@user_passes_test(admin_check)
def reports_dashboard(request):
    total_customers = Customer.objects.count()
    total_orders = Order.objects.count()
    total_bookings = Booking.objects.count()

    context = {
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_bookings': total_bookings,
    }
    return render(request, 'adminpanel/reports_dashboard.html', context)


@login_required
@user_passes_test(admin_check)
def customer_report(request):
    customers = Customer.objects.select_related('user').order_by('customer_id')
    context = {
        'customers': customers,
        'title': 'Customer Report',
    }
    return render(request, 'adminpanel/customer_report.html', context)


@login_required
@user_passes_test(admin_check)
def order_report(request):
    orders = Order.objects.select_related('customer').order_by('-order_date')
    context = {
        'orders': orders,
        'title': 'Order Report',
    }
    return render(request, 'adminpanel/order_report.html', context)


@login_required
@user_passes_test(admin_check)
def booking_report(request):
    bookings = Booking.objects.select_related('customer', 'service', 'staff').order_by('-booked_at')
    context = {
        'bookings': bookings,
        'title': 'Booking Report',
    }
    return render(request, 'adminpanel/booking_report.html', context)