from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),

    path('deliveries/', views.delivery_list, name='admin_deliveries'),
    path('deliveries/<int:pk>/update/', views.delivery_update, name='admin_delivery_update'),

    path('reports/', views.reports_dashboard, name='admin_reports'),
    path('reports/customers/', views.customer_report, name='admin_customer_report'),
    path('reports/orders/', views.order_report, name='admin_order_report'),
    path('reports/bookings/', views.booking_report, name='admin_booking_report'),

    path('<str:module>/', views.general_list, name='admin_list'),
    path('<str:module>/add/', views.general_form, name='admin_add'),
    path('<str:module>/edit/<int:pk>/', views.general_form, name='admin_edit'),
    path('<str:module>/delete/<int:pk>/', views.general_delete, name='admin_delete'),
]
