from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.booking_view, name='booking'),
    path('booking/success/<int:booking_id>/', views.booking_success_view, name='booking_success'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
]
