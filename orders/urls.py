from django.urls import path
from . import views

urlpatterns = [
    path('buy-now/<int:product_id>/',     views.buy_now,            name='buy_now'),
    path('checkout/',                     views.checkout,           name='checkout'),
    path('payment/verify/',               views.payment_verify,     name='payment_verify'),
    path('order/<int:order_id>/confirm/', views.order_confirmation,  name='order_confirmation'),
    path('my-orders/',                    views.my_orders,          name='my_orders'),
    path('invoice/<int:order_id>/download/', views.download_invoice, name="download_invoice")
]
