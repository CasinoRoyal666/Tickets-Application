from django.contrib import admin
from .models import Event, EventImage, Order, OrderItem
from django.utils.html import format_html

class EventImageAdmin(admin.StackedInline):
    model = EventImage
    extra = 1
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Preview"

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'price', 'available_tickets', 'tickets_status')
    search_fields = ('title', 'description')
    list_filter = ('date', 'category')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields' : ('title', 'description', 'category')
        }),
        ('Details', {
            'fields' : ('date', 'location', 'price', 'available_tickets') 
        }),
        ('System Information', {
            'fields' : ('created_at', 'updated_at')
        })
    )

    inlines = [EventImageAdmin]

    def tickets_status(self,obj):
        if obj.available_tickets == 0:
            color = 'red'
            status = 'Sold Out'
        elif obj.available_tickets < 50:
            color = 'yellow'
            status = 'Few tickets left'
        else:
            color = 'green'
            status = 'In Stock'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    tickets_status.short_description = "Ticket Status"

admin.site.register(Event, EventAdmin)
admin.site.register(Order)