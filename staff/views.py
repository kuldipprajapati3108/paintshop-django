from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q

from .models import Staff
from orders.models import Delivery, Order
from accounts.models import Customer
from services.models import Booking


def staff_check(user):
    """Check if user is a staff member."""
    if not user.is_authenticated:
        return False
    # Must be marked as staff in Django auth AND have a Staff profile
    if not user.is_staff:
        return False
    try:
        Staff.objects.get(user=user)
        return True
    except Staff.DoesNotExist:
        return False


@login_required
@user_passes_test(staff_check)
def staff_dashboard(request):
    """Staff dashboard - shows summary based on role."""
    staff = get_object_or_404(Staff, user=request.user)

    context = {
        "staff": staff,
        "role": staff.role,
    }

    # Role-specific data
    if staff.role == "delivery":
        # Delivery staff: show their delivery stats
        today = timezone.now().date()
        deliveries = Delivery.objects.filter(staff=staff)

        context.update(
            {
                "total_deliveries": deliveries.count(),
                "pending_deliveries": deliveries.filter(
                    delivery_status="pending"
                ).count(),
                "assigned_deliveries": deliveries.filter(
                    delivery_status="assigned"
                ).count(),
                "out_for_delivery": deliveries.filter(
                    delivery_status="out_for_delivery"
                ).count(),
                "delivered_today": deliveries.filter(
                    delivery_status="delivered", delivery_date=today
                ).count(),
                "recent_deliveries": deliveries.order_by("-order__order_date")[:5],
            }
        )

    elif staff.role == "painter":
        # Painter staff: show their assigned services/bookings
        # (bookings with staff assigned and status not completed)
        from services.models import Booking

        bookings = Booking.objects.filter(staff=staff)

        context.update(
            {
                "total_jobs": bookings.count(),
                "pending_jobs": bookings.filter(
                    status__in=["pending", "confirmed"]
                ).count(),
                "in_progress_jobs": bookings.filter(status="in_progress").count(),
                "completed_jobs": bookings.filter(status="completed").count(),
                "recent_jobs": bookings.order_by("-service_date")[:5],
            }
        )

    elif staff.role == "manager":
        # Manager: show overview
        total_staff = Staff.objects.count()
        available_staff = Staff.objects.filter(availability_status="available").count()
        total_deliveries = Delivery.objects.count()
        pending_deliveries = Delivery.objects.filter(delivery_status="pending").count()

        context.update(
            {
                "total_staff": total_staff,
                "available_staff": available_staff,
                "total_deliveries": total_deliveries,
                "pending_deliveries": pending_deliveries,
                "recent_deliveries": Delivery.objects.select_related(
                    "order", "order__customer", "staff"
                ).order_by("-order__order_date")[:10],
                "recent_bookings": (
                    Booking.objects.select_related("customer", "service").order_by(
                        "-booked_at"
                    )[:10]
                    if hasattr(request, "Booking")
                    else []
                ),
            }
        )

    return render(request, "staff/dashboard.html", context)


@login_required
@user_passes_test(staff_check)
def staff_deliveries(request):
    """List all deliveries assigned to the staff member."""
    staff = get_object_or_404(Staff, user=request.user)

    # Filter by status if provided
    status_filter = request.GET.get("status", "")

    deliveries = (
        Delivery.objects.filter(staff=staff)
        .select_related("order", "order__customer")
        .order_by("-order__order_date")
    )

    if status_filter:
        deliveries = deliveries.filter(delivery_status=status_filter)

    # Get status counts for badges
    status_counts = deliveries.values("delivery_status").annotate(
        count=Count("delivery_id")
    )

    context = {
        "staff": staff,
        "deliveries": deliveries,
        "status_filter": status_filter,
        "status_counts": {s["delivery_status"]: s["count"] for s in status_counts},
        "status_choices": Delivery.DELIVERY_STATUS_CHOICES,
    }

    return render(request, "staff/deliveries.html", context)


@login_required
@user_passes_test(staff_check)
def staff_delivery_update(request, pk):
    """Update delivery status by staff."""
    staff = get_object_or_404(Staff, user=request.user)

    # Get delivery and verify it belongs to this staff
    delivery = get_object_or_404(
        Delivery.objects.select_related("order", "order__customer"), pk=pk, staff=staff
    )

    order = delivery.order

    if request.method == "POST":
        new_status = request.POST.get("delivery_status")
        delivery_notes = request.POST.get("delivery_notes", "").strip()

        # Update delivery
        delivery.delivery_status = new_status
        if new_status == "delivered":
            delivery.delivery_date = timezone.now().date()
        delivery.save()

        # Update order status if needed
        if new_status == "delivered":
            order.status = "completed"
            order.save()
        elif new_status == "failed":
            order.status = "cancelled"
            order.save()

        messages.success(
            request,
            f"Delivery #{delivery.delivery_id} status updated to {delivery.get_delivery_status_display()}.",
        )
        return redirect("staff_deliveries")

    # Get order items for display
    items = order.items.all()
    total = order.total_amount

    context = {
        "staff": staff,
        "delivery": delivery,
        "order": order,
        "items": items,
        "total": total,
        "status_choices": Delivery.DELIVERY_STATUS_CHOICES,
    }

    return render(request, "staff/delivery_update.html", context)
