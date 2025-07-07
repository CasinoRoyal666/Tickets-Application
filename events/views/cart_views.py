from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from events.serializers.cart_serializers import CartItemSerializer
from events.services.cart_services import CartService


class CartViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        cart = request.session.get('cart', {})
        cart_contents = CartService.get_cart_contents(cart)
        return Response(cart_contents)

    def create(self, request):
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        event_id = serializer.validated_data['event_id']
        quantity = serializer.validated_data['quantity']
        
        cart = request.session.get('cart', {})
        cart = CartService.add_to_cart(cart, event_id, quantity)
        request.session['cart'] = cart
        
        return self.list(request)

    def destroy(self, request, pk=None):
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
        request.session['cart'] = CartService.clear_cart()
        return Response(
            {'message': 'Cart cleared'}, 
            status=status.HTTP_200_OK
        )