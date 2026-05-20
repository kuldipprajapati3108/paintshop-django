from django.contrib import admin
from .models import *

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'feedback_id',
        'customer',
        'product',
        'service',
        'rating',
        'created_at'
    )
    list_filter = ('rating',)
    readonly_fields = ('created_at',)