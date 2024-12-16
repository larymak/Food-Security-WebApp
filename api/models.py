from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point

# Create your models here.

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('donor', 'Donor'),
        ('recipient', 'Recipient'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)

    def __str__(self):
        return self.username
    
    def role(self):
        return self.get_user_type_display()

class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization_name = models.CharField(max_length=100, null=True, blank=True)
    contact_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    location = gis_models.PointField(null=True, blank=True)

    def __str__(self):
        return f"Donor: {self.user.username}"

    def set_location(self, latitude, longitude):
        self.location = Point(longitude, latitude)
        self.save()

class Recipient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    location = gis_models.PointField(null=True, blank=True)

    def __str__(self):
        return f"Recipient: {self.user.username}"

    def set_location(self, latitude, longitude):
        self.location = Point(longitude, latitude)
        self.save()

class FoodItem(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilograms'),
        ('liters', 'Liters'),
        ('crates', 'Crates'),
        ('tray', 'Tray'),
        ('dozen', 'Dozen'),
        # Add more units as needed
    ]
    food_name = models.CharField(max_length=100, unique=True)
    quantity = models.PositiveIntegerField(default=0)  # Ensure quantity is positive
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.food_name} ({self.quantity} {self.unit})"

class Donation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
    ]
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    donation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    expiry_date = models.DateField(default=None, null=True, blank=True)

    def __str__(self):
        return f"{self.donor.username}'s donation of {self.food_item.food_name}"

class Request(models.Model):
    STATUS_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    pickup_date = models.DateField(default=None, null=True, blank=True)
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='low')
    donation = models.ForeignKey(Donation, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Request by {self.recipient.username} for {self.quantity} {self.food_item.food_name}"

class Delivery(models.Model):
    DELIVERY_STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='in_progress')
    delivery_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delivery for Request {self.request.id} and Donation {self.donation.id}"

class DeliveryTracking(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tracking for Delivery {self.delivery.id} at {self.timestamp}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=50)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.notification_type}"

class TransactionHistory(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('donation', 'Donation'),
        ('request', 'Request'),
        ('delivery', 'Delivery'),
    ]
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction: {self.transaction_type} on {self.transaction_date}"

class Matching(models.Model):
    MATCH_STATUS_CHOICES = [
        ('matched', 'Matched'),
        ('unmatched', 'Unmatched'),
    ]
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    matched_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=MATCH_STATUS_CHOICES, default='matched')

    def __str__(self):
        return f"Match between Donation {self.donation.id} and Request {self.request.id}"
