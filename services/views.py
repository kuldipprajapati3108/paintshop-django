from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Prefetch
from decimal import Decimal

from accounts.models import Customer
from services.models import Service, Booking


@login_required(login_url='login')
def booking_view(request):
    """Display the booking form and handle submissions."""
    customer = get_object_or_404(Customer, user=request.user)

    # Fetch all active services
    services = Service.objects.all().order_by('service_name')

    if request.method == 'POST':
        # Validate form data
        service_id = request.POST.get('service')
        area_sqft = request.POST.get('area_sqft')
        service_date = request.POST.get('service_date')
        address = request.POST.get('address', '').strip()

        # Validation
        errors = []

        if not service_id:
            errors.append("Please select a service.")
        else:
            try:
                service = Service.objects.get(service_id=service_id)
            except Service.DoesNotExist:
                errors.append("Invalid service selected.")
        if not area_sqft:
            errors.append("Please enter the area.")
        else:
            try:
                area_sqft = Decimal(area_sqft)
                if area_sqft <= 0:
                    errors.append("Area must be greater than 0.")
            except (ValueError, Decimal.InvalidOperation):
                errors.append("Please enter a valid area.")

        if not service_date:
            errors.append("Please select a service date.")
        else:
            try:
                from datetime import datetime
                service_date_obj = datetime.strptime(service_date, '%Y-%m-%d').date()
                if service_date_obj < timezone.now().date():
                    errors.append("Service date cannot be in the past.")
            except ValueError:
                errors.append("Invalid date format.")

        if not address:
            errors.append("Please enter the delivery address.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'services/booking.html', {
                'services': services,
                'customer': customer,
                'today': timezone.now().date(),
            })

        # Calculate estimated price
        estimated_price = service.price_per_sq * area_sqft

        # Create booking
        booking = Booking.objects.create(
            customer=customer,
            service=service,
            area_sqft=area_sqft,
            estimated_price=estimated_price,
            service_date=service_date_obj,
            address=address,
            status='pending',  # Pending until admin confirms
            booked_at=timezone.now(),
        )

        # Success! Redirect to success page
        messages.success(request, f"Booking #{booking.booking_id} created successfully!")
        return redirect('booking_success', booking_id=booking.booking_id)

    # GET request - show form
    context = {
        'services': services,
        'customer': customer,
        'today': timezone.now().date(),
    }
    return render(request, 'services/booking.html', context)


@login_required(login_url='login')
def booking_success_view(request, booking_id):
    """Display booking confirmation/success page."""
    customer = get_object_or_404(Customer, user=request.user)
    booking = get_object_or_404(
        Booking.objects.select_related('service', 'product', 'color', 'staff'),
        booking_id=booking_id,
        customer=customer
    )

    return render(request, 'services/booking_success.html', {
        'booking': booking,
    })


@login_required(login_url='login')
def my_bookings(request):
    """Display all bookings for the logged-in customer."""
    customer = get_object_or_404(Customer, user=request.user)

    # Optimized query: fetch bookings with all related data in 2 queries
    bookings = (Booking.objects
                .filter(customer=customer)
                .select_related('service', 'product', 'color', 'staff')
                .order_by('-booked_at'))

    return render(request, 'services/my_bookings.html', {
        'bookings': bookings,
    })
