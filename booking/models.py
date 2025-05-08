from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import date

class User(AbstractUser):
    
    fullname = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username



class ServiceCategory(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Service Categories"

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_hours = models.PositiveIntegerField(default=0, help_text="Duration hours")
    duration_minutes = models.PositiveIntegerField(default=0, help_text="Duration minutes")
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    @property
    def total_duration_minutes(self):
        return self.duration_hours * 60 + self.duration_minutes

    class Meta:
        ordering = ['category', 'name']

class Schedule(models.Model):
    
    available_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    capacity = models.PositiveIntegerField(default=1, help_text="Max bookings per slot (number of staff available)")

    def __str__(self):
        return f"{self.available_time.strftime('%I:%M %p')}, Slots: {self.capacity}"
    
    class Meta:
        ordering = ["available_time"]


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField(default=date.today)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    booking_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"#{self.id} - {self.service.name} for {self.user.username} on {self.date} at {self.schedule.available_time.strftime('%I:%M %p')}"

    class Meta:
        ordering = ['-date', '-booking_time']

class BookingLine(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('inprogress', 'Inprogress'),
        ('completed', 'Completed'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_lines')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.service.name} for {self.booking.user.username}"

# Online payment only (GCash or PayPal)
class Payment(models.Model):
    PAYMENT_METHODS = [
        ('gcash', 'GCash'),
        ('paypal', 'PayPal'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment via {self.get_method_display()} for Booking #{self.booking.id}"


# Ratings and comments for services
class Feedback(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'booking')

    def __str__(self):
        return f'Feedback by {self.user} for {self.service} (booking #{self.booking.id if self.booking else "No Booking"})'
    
class Receipt(models.Model):
    payment = models.OneToOneField('Payment', on_delete=models.CASCADE, related_name='receipt')
    issued_at = models.DateTimeField(auto_now_add=True)
    number = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return f"Receipt {self.number} for Payment {self.payment.id}"

