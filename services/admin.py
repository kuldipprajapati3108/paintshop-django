from django.contrib import admin
from .models import *

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_id','service_name','price_per_sq','description')
    search_fields = ('service_name',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id','customer','service','service_date','area_sqft','status','staff')
    list_filter = ('service_date','status')

