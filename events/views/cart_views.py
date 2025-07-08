from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from events.serializers.cart_serializers import CartItemSerializer
from events.services.cart_services import CartService


class CartViewSet(viewsets.ViewSet):
    """ViewSet for managing shopping cart operations

    Provides functionality for viewing, adding, removing, and clearing items in the cart.
    Cart data is stored in the user's session.

    Permissions:
        AllowAny
    """
    permission_classes = [AllowAny]

    def list(self, request):
        """Retrieve the contents of the cart

        Fetches the cart from the session and returns its contents in a serialized format

        Attributes:
            request: HTTP request

        Returns:
            Response: JSON representation of cart contents
        """
        cart = request.session.get('cart', {})
        cart_contents = CartService.get_cart_contents(cart)
        return Response(cart_contents)

    def create(self, request):
        """Add an item to the cart

        Validates the input data (event ID and quantity). Cart working with the session tocken.

        Attributes:
            request: HTTP request containing event_id and quantity

        Returns:
            Response: JSON representation of updated cart contents
        """
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        event_id = serializer.validated_data['event_id']
        quantity = serializer.validated_data['quantity']
        
        cart = request.session.get('cart', {})
        cart = CartService.add_to_cart(cart, event_id, quantity)
        request.session['cart'] = cart
        
        return self.list(request)

    def destroy(self, request, pk=None):
        """Remove an item from the cart

        Attributes:
            request: HTTP request
            pk (str): Event ID of the item to remove

        Returns:
            Response: Status 204 if the item was removed, or 404 if the item was not found
        """
        cart = request.session.get('cart', {})
        cart, removed = CartService.remove_from_cart(cart, pk)
        
        if removed:
            request.session['cart'] = cart
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'error': 'Item not found in cart'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear all items from the cart

        Attributes:
            request: HTTP request

        Returns:
            Response: JSON message confirming the cart was cleared with status 200
        """
        request.session['cart'] = CartService.clear_cart()
        return Response(
            {'message': 'Cart cleared'}, 
            status=status.HTTP_200_OK
        )