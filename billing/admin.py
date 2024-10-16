from django.contrib import admin
from .models import Zone, Collector, Customer, Payment, Expense

@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Collector)
class CollectorAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'phone', 'referral_code')
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Name'
    
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'customer_id', 'zone', 'is_paid')
    list_filter = ('is_paid', 'zone')
    search_fields = ('name', 'phone', 'customer_id')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'collector', 'date')
    list_filter = ('date', 'collector')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'date')
    list_filter = ('date',)
