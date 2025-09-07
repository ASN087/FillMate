from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'content_object', 'created_at', 'is_read')
    list_filter = ('is_read', 'recipient')
    search_fields = ('sender__username', 'recipient__username')
    readonly_fields = ('content_object',)
    
    def content_object(self, obj):
        return str(obj.content_object)
    content_object.short_description = 'Document'