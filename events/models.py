from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class EventCategory(models.TextChoices):
        CONCERT = 'concert', 'Concert'
        SPORTS = 'sports', 'Sports'
        THEATER = 'theater', 'Theater'
        PRESENTATION = 'presentation', 'Presentation'
        CONFERENCE = 'conference', 'Conference'
        OTHER = 'other', 'Other'

class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CANCELLED = 'cancelled', 'Cancelled'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Event(BaseModel):
    title = models.CharField(max_length=120)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=EventCategory.choices, default=EventCategory.OTHER)
    date = models.DateTimeField()
    location = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal(0.00))])
    available_tickets = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'event'
        verbose_name_plural = 'events'
        ordering = ['date']

    def __str__(self):
        return self.title
    
class EventImage(BaseModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='event_images/')

    class Meta:
        verbose_name = 'eventImage'
        verbose_name_plural = 'eventImages'
    
    def __str__(self):
        return f"Image for {self.event.title}"
    
class Order(BaseModel):   
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=25)
    customer_phone =models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    class Meta:
        verbose_name = 'order'
        verbose_name_plural = 'orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"
    
class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        verbose_name = 'item'
        verbose_name_plural = 'items'
    
    def __str__(self):
        return f"{self.quantity}x {self.event.title}"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
