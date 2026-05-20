from django.contrib import admin
from .models import *

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id','offer_id','customer','order_date','status')
    list_filter = ('status',)
    readonly_fields = ('order_date',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_item_id','order','product','color','quantity','price')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id','order','booking','payment_method','status','amount','payment_date')
    list_filter = ('status','payment_method')
    readonly_fields = ('payment_date',)

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('delivery_id','order','staff','delivery_status','delivery_date')
    list_filter = ('delivery_status',)
