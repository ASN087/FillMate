from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class Notification(models.Model):
    # Recipient (always a HOD)
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='notifications_received'
    )
    
    # Submitter (user who sent the document)
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications_sent',
        verbose_name='Submitted By'
    )
    
    # Document reference (generic relationship)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Core fields
    message = models.CharField(max_length=200)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document Submission Alert'

    def __str__(self):
        return f"New doc from {self.sender} to {self.recipient}"