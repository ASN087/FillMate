from django.contrib.contenttypes.models import ContentType
from .models import Notification

def notify_document_submission(submitted_doc, sender):
    """Create notifications for HODs when docs are submitted"""
    from django.contrib.auth.models import Group
    
    # Get the document's content type
    doc_type = ContentType.objects.get_for_model(submitted_doc)
    
    # Notify all HODs
    hod_group = Group.objects.get(name='HOD')
    for hod in hod_group.user_set.all():
        Notification.objects.create(
            recipient=hod,
            sender=sender,
            content_type=doc_type,
            object_id=submitted_doc.id,
            message=f"New {submitted_doc.__class__.__name__} submitted by {sender.username}"
        )