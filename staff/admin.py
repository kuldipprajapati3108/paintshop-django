from django.contrib import admin
from .models import *

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('staff_id','user','full_name','role','phone','email','availability_status')
    list_filter = ('role','availability_status')
    search_fields = ('full_name',)
    readonly_fields = ('created_at',)