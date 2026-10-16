from django.db import models
from django.contrib.auth.models import User

class Agent(models.Model):
    # Links this Agent to a built-in Django User account for login purposes
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Property(models.Model):
    # These choices will populate our dropdown filters later
    PROPERTY_TYPES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('condo', 'Condo'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2) # e.g., 750000.00
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default='house')
    bedrooms = models.IntegerField()
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1) # Allows for 2.5 baths
    square_feet = models.IntegerField()
    year_built = models.IntegerField()

    # Requires the 'Pillow' package we installed earlier
    image = models.ImageField(upload_to='property_images/', blank=True, null=True)

    # Connects each property to exactly one Agent
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='properties')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Conversation(models.Model):
    """One tour request / chat between a client and the agent who owns the listing."""
    STATUS = [('pending', 'Pending'), ('confirmed', 'Confirmed'), ('declined', 'Declined')]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='conversations')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tour_chats')
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='chats')
    preferred_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('property', 'client')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.client} - {self.property}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
