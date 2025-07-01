from rest_framework import serializers
from .models import  Event, EventImage, Order, OrderItem
from .services import create_order

class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ['id','image','created_at']
        read_only_fields = ['id','created_at']

class EventSerializer(serializers.ModelSerializer):
    images = EventImageSerializer(many=True, read_only=True)
    category_display = serializers.CharField(source ='get_category_display', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category', 'category_display', 'date', 'location', 'price',
            'available_tickets', 'images', 'created_at', 'updated_at'
        ]

class EventListSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source ='get_category_display', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'category', 'category_display', 'date', 'location', 'price', 'available_tickets'
        ]

class OrderItemSerializer(serializers.ModelSerializer):  
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateTimeField(source = 'event.date', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'event', 'event_title', 'event_date',
            'quantity', 'unit_price', 'total_price'
        ]
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'customer_email', 'customer_name', 'customer_phone', 'status',
            'status_display', 'total_price', 'items', 'created_at', 'updated_at'
        ]

class OrderItemCreateSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    class Meta:
        model = OrderItem
        fields = ['event', 'quantity']\

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['customer_email', 'customer_name', 'customer_phone', 'items']
