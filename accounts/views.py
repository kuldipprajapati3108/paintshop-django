from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Customer
from orders.models import Order, OrderItem, Payment, Delivery


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            if user.is_superuser:
                return redirect("admin_dashboard")
            elif user.is_staff:
                return redirect("staff_dashboard")
            return redirect("home")

        messages.error(request, "Invalid details")

    return render(request, "accounts/login.html", {"hide_navbar": True})


def logout_view(request):
    user = request.user
    logout(request)

    if user.is_staff or user.is_superuser:
        return redirect("login")
    else:
        return redirect("home")


def register_view(request):

    if request.method == "POST":

        fullname = request.POST.get("fullname", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        mobile = request.POST.get("mobile", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()

        context = {"hide_navbar": True, "form_data": request.POST}

        if not all([fullname, username, password, confirm_password, mobile, email]):
            messages.error(request, "All fields are required.")
            return render(request, "accounts/register.html", context)

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, "accounts/register.html", context)

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/register.html", context)

        if len(mobile) != 10 or not mobile.isdigit():
            messages.error(request, "Mobile number must be 10 digits.")
            return render(request, "accounts/register.html", context)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "accounts/register.html", context)

        if Customer.objects.filter(phone=mobile).exists():
            messages.error(request, "Mobile number already registered.")
            return render(request, "accounts/register.html", context)

        if Customer.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "accounts/register.html", context)

        created_user = User.objects.create_user(
            username=username, password=password, email=email
        )
        Customer.objects.create(
            user=created_user,
            cust_name=fullname,
            email=email,
            phone=mobile,
            address=address,
        )

        auth_user = authenticate(request, username=username, password=password)
        if auth_user:
            login(request, auth_user)

        messages.success(request, "Registration successful!")
        return redirect("home")

    return render(request, "accounts/register.html", {"hide_navbar": True})


def profile_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        customer = Customer.objects.get(user=request.user)

        if action == "update_profile":
            customer.cust_name = request.POST.get("cust_name", customer.cust_name)
            customer.phone = request.POST.get("phone", customer.phone)
            customer.address = request.POST.get("address", customer.address)
            customer.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")

        elif action == "change_password":
            user = request.user
            current_password = request.POST.get("current_password")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            if not user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
                return redirect("profile")

            if len(new_password) < 8:
                messages.error(request, "New password must be at least 8 characters.")
                return redirect("profile")

            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect("profile")

            user.set_password(new_password)
            user.save()
            messages.success(request, "Password changed successfully!")
            return redirect("login")

    customer = Customer.objects.get(user=request.user)

    # Get order statistics
    orders = Order.objects.filter(customer=customer)
    total_orders = orders.count()
    completed_orders = orders.filter(status="completed").count()
    pending_orders = orders.filter(status__in=["pending", "processing"]).count()

    context = {
        "customer": customer,
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders,
    }

    return render(request, "accounts/profile.html", context)
