from django.urls import path
from . import views

urlpatterns = [
    path('product/<int:product_id>/', views.product_feedback, name='product_feedback'),
    path('add/<int:product_id>/', views.add_feedback, name='add_feedback'),
    path('order/<int:order_id>/', views.order_feedback, name='order_feedback'),
]
