from django.contrib import admin
from .models import Plan, Voucher, Payment
# Register your models here.

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_hours', 'price', 'data_limit_mb', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('duration_hours', 'price')
    ordering = ('-created_at',)
    
@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'plan', 'used', 'user', 'created_at')
    search_fields = ('code', 'plan__name', 'user__username')
    list_filter = ('used', 'plan')
    ordering = ('-created_at',) 
    
    
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('mpesa_code', 'user', 'plan', 'amount', 'status', 'timestamp')
    search_fields = ('mpesa_code', 'user__username', 'plan__name')
    list_filter = ('status', 'plan')
    ordering = ('-timestamp',)