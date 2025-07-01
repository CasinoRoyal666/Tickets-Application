from .models import Order, OrderItem

def create_order(validated_data):
    items_data = validated_data.pop('items', [])
    order = Order.objects.create(**validated_data)

    for item_data in items_data:
        OrderItem.objects.create(
            order=order,
            event=item_data['event'],
            quantity=item_data['quantity']
        )
    return order