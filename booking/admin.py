
from django.contrib import admin
from .models import (
    User, ServiceCategory, Service, Schedule, Booking, Payment, Feedback, BookingLine,Receipt
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'fullname', 'is_admin', 'is_staff', 'is_superuser', 'created_at', 'date_joined', 'last_login')
    search_fields = ('username', 'email', 'fullname')
    list_filter = ('is_admin', 'is_staff', 'is_superuser')
    ordering = ('-created_at',)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'description', 'price', 'duration_hours', 'duration_minutes', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('category', 'name')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "available_time", "is_available", "capacity")
    ordering = ["available_time"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'date', 'schedule', 'booking_time')
    list_filter = ('date', 'service')
    search_fields = ('user__username', 'service__name')
    ordering = ('-date', '-booking_time')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'user', 'method', 'transaction_id', 'amount', 'payment_date')
    list_filter = ('method', 'payment_date')
    search_fields = ('booking__id', 'user__username', 'transaction_id')
    ordering = ('-payment_date',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'service', 'user', 'rating', 'comment', 'created_at')
    list_filter = ('rating', 'service')
    search_fields = ('service__name', 'user__username', 'comment')
    ordering = ('-created_at',)

@admin.register(BookingLine)
class BookingLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'service', 'status')
    list_filter = ('status', 'service')
    search_fields = ('booking__id', 'service__name')
    ordering = ('booking', 'service')

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'issued_at')
    list_filter = ('issued_at',)
    search_fields = (
        'payment__booking__id',
        'payment__booking__user__username',
        'payment__amount',
        'number',
    )
    ordering = ('-issued_at',)
    readonly_fields = (
        'number', 'issued_at', 'booking', 'user', 'service', 'amount',
        'payment_method', 'transaction_id'
    )

    fieldsets = (
        (None, {
            'fields': (
                'number', 'issued_at', 'booking', 'user', 'service',
                'amount', 'payment_method', 'transaction_id'
            )
        }),
    )

    @admin.display(ordering='payment__booking', description='Booking')
    def booking(self, obj):
        if obj.payment and obj.payment.booking:
            booking = obj.payment.booking
            return f'#{booking.id} - {booking.user.username}'
        return '-'

    @admin.display(description='User')
    def user(self, obj):
        if obj.payment and obj.payment.booking:
            return obj.payment.booking.user.username
        return '-'

    @admin.display(description='Service')
    def service(self, obj):
        if obj.payment and obj.payment.booking:
            return obj.payment.booking.service.name
        return '-'

    @admin.display(ordering='payment__amount', description='Amount')
    def amount(self, obj):
        return obj.payment.amount if obj.payment else '-'

    @admin.display(description='Payment Method')
    def payment_method(self, obj):
        return obj.payment.method if obj.payment else '-'

    @admin.display(description='Transaction ID')
    def transaction_id(self, obj):
        return obj.payment.transaction_id if obj.payment else '-'
