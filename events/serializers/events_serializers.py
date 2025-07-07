from rest_framework import serializers
from events.models import Event, EventImage


class EventImageSerializer(serializers.ModelSerializer):
    """Serializer for event images

    Attributes:
        id (int): The ID of the image;
        image (ImageField): The uploaded image file;
        created_at (DateTimeField): The timestamp when the image was created.
    """
    class Meta:
        model = EventImage
        fields = ['id', 'image', 'created_at']
        read_only_fields = ['id', 'created_at']


class EventSerializer(serializers.ModelSerializer):
    """Serializer for detailed event data

    Attributes:
        id (int): The ID of the event;
        title (str): The title of the event;
        description (str): The description of the event;
        category (str): The category of the event;
        category_display (str): The human-readable category name;
        date (DateTimeField): The date and time of the event;
        location (str): The location of the event;
        price (DecimalField): The price of the event tickets;
        available_tickets (int): The number of available tickets;
        images (List[EventImageSerializer]): Nested serializer for event images;
        created_at (DateTimeField): The timestamp when the event was created;
        updated_at (DateTimeField): The timestamp when the event was last updated.
    """
    images = EventImageSerializer(many=True, read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category', 'category_display', 'date', 'location', 'price',
            'available_tickets', 'images', 'created_at', 'updated_at'
        ]


class EventListSerializer(serializers.ModelSerializer):
    """Serializer for a list of events.

    Сontains brief information about the event and is used when there are many of them

    Attributes:
        id (int): The ID of the event;
        title (str): The title of the event;
        category (str): The category of the event;
        category_display (str): The human-readable category name;
        date (DateTimeField): The date and time of the event;
        location (str): The location of the event;
        price (DecimalField): The price of the event tickets;
        available_tickets (int): The number of available tickets;
    """
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'category', 'category_display', 'date', 'location', 'price', 'available_tickets'
        ]