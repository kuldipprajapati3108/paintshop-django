from django.urls import path
from . import views

urlpatterns = [
    path('', views.staff_dashboard, name='staff_dashboard'),
    path('deliveries/', views.staff_deliveries, name='staff_deliveries'),
    path('delivery/update/<int:pk>/', views.staff_delivery_update, name='staff_delivery_update'),
]
