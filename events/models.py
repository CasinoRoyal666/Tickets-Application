from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Event(BaseModel):
    CATEGORY_CHOISES = [
        ('concert', 'Concert'),
        ('sports', 'Sports'),
        ('theater' , 'Theater'),
        ('presentation' , 'Presentation'),
        ('conference' , 'Conderence'),
        ('show' , 'Show'),
        ('other' , 'Other'),
    ]
    event_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=120)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOISES)
    date = models.DateTimeField()
    location = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal(0.00))])
    available_tickets = models.PositiveIntegerField()

    class Meta:
        db_table = 'events_event'
        ordering = ['date']

    def __str__(self):
        return self.title
    
class EventImage(BaseModel):
    image_id = models.AutoField(primary_key=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image_url = models.ImageField(upload_to='event_images/')

    class Meta:
        db_table = 'events_eventimage'
    
    def __str__(self):
        return f"Image for {self.event.title}"
    
class Order(BaseModel):
    STATUS_CHOISES = [
        ('pending' , 'Pending'),
        ('cancelled' , 'Cancelle3d'),
        ('confirmed' , 'Confirmed'),
        ('completed' , 'Completed'),
    ]
    order_id = models.AutoField(primary_key=True) 
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=25)
    customer_phone =models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    status = models.CharField(max_length=20, choices=STATUS_CHOISES, default='pending')

    class Meta:
        db_table = 'events_order'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_id} - {self.customer_name}"
    
class OrderItem(BaseModel):
    item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        db_table = 'events_orderitem'
    
    def __str__(self):
        return f"{self.quantity}x {self.event.title}"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
