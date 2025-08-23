from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Stock, Portfolio, Holding, Transaction


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_verified', 'risk_tolerance', 'created_at']
    list_filter = ['is_verified', 'risk_tolerance', 'investment_experience', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Trading Profile', {
            'fields': ('phone_number', 'date_of_birth', 'is_verified', 'risk_tolerance', 'investment_experience')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    
    list_display = ['symbol', 'name', 'exchange', 'current_price', 'day_change_percent', 'volume', 'is_active']
    list_filter = ['exchange', 'sector', 'industry', 'is_active']
    search_fields = ['symbol', 'name', 'sector', 'industry']
    readonly_fields = ['created_at', 'updated_at', 'last_price_update']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('symbol', 'name', 'exchange', 'sector', 'industry', 'market_cap', 'is_active')
        }),
        ('Market Data', {
            'fields': ('current_price', 'previous_close', 'day_change', 'day_change_percent')
        }),
        ('Trading Info', {
            'fields': ('volume', 'avg_volume', 'pe_ratio', 'dividend_yield')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_price_update'),
            'classes': ('collapse',)
        }),
    ]


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'total_value', 'cash_balance', 'is_default', 'is_active', 'created_at']
    list_filter = ['is_default', 'is_active', 'created_at']
    search_fields = ['name', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('user', 'name', 'description', 'is_default', 'is_active')
        }),
        ('Financial Metrics', {
            'fields': ('total_value', 'cash_balance', 'invested_amount', 'total_return', 'total_return_percent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]


class HoldingInline(admin.TabularInline):
    model = Holding
    extra = 0
    readonly_fields = ['current_value', 'unrealized_gain_loss', 'unrealized_gain_loss_percent']


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'stock', 'quantity', 'average_cost', 'current_value', 'unrealized_gain_loss_percent']
    list_filter = ['portfolio__user', 'stock__sector']
    search_fields = ['portfolio__name', 'stock__symbol', 'stock__name']
    readonly_fields = ['current_value', 'unrealized_gain_loss', 'unrealized_gain_loss_percent', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Position', {
            'fields': ('portfolio', 'stock', 'quantity', 'average_cost', 'total_cost')
        }),
        ('Performance', {
            'fields': ('current_value', 'unrealized_gain_loss', 'unrealized_gain_loss_percent')
        }),
        ('Dates', {
            'fields': ('first_purchase_date', 'last_transaction_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'stock', 'transaction_type', 'quantity', 'price', 'total_amount', 'status', 'transaction_date']
    list_filter = ['transaction_type', 'status', 'transaction_date', 'portfolio__user']
    search_fields = ['portfolio__name', 'stock__symbol', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'transaction_date'
    
    fieldsets = [
        ('Transaction Details', {
            'fields': ('portfolio', 'stock', 'transaction_type', 'status')
        }),
        ('Financial Details', {
            'fields': ('quantity', 'price', 'total_amount', 'fees')
        }),
        ('Timing', {
            'fields': ('transaction_date',)
        }),
        ('Additional Info', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]