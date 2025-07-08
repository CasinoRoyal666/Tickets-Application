# events/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from events.views.cart_views import CartViewSet
from events.views.events_views import EventViewSet
from events.views.orders_views import OrderViewSet

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'cart', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]