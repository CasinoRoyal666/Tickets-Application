# events/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from events.views.cart_views import CartViewSet
from events.views.events_views import EventViewSet, EventImageViewSet
from events.views.orders_views import OrderViewSet, OrderItemViewSet

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'event-images', EventImageViewSet, basename='eventimages')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='orderitem')
router.register(r'cart', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]