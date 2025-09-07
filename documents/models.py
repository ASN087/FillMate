from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.models import User

User = get_user_model()

class DocumentTemplate(models.Model):
    """Model to store document templates"""
    name = models.CharField(max_length=255, unique=True)  # Template name
    file = models.FileField(upload_to='templates/')  # DOCX file storage
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp

    def __str__(self):
        return self.name

class Placeholder(models.Model):
    """Model to store placeholders for document templates"""
    
    TYPE_CHOICES = [
        ('text', 'Text'),
        ('date', 'Date'),
    ]

    template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE, related_name="placeholders")
    name = models.CharField(max_length=255)  # e.g., case_number, accused_name
    placeholder_text = models.CharField(max_length=255)  # e.g., <case_number>, <accused_name>
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='text')  # New: Type field
    example = models.CharField(max_length=255, blank=True, null=True)  # New: Example field

    def __str__(self):
        return f"{self.name} ({self.placeholder_text})"

# ✅ Fix: Move the import inside the function to prevent circular import
@receiver(post_save, sender=DocumentTemplate)
def extract_placeholders_signal(sender, instance, created, **kwargs):
    if created:  # Only extract for newly uploaded templates
        print(f"📄 New template uploaded: {instance.name}. Extracting placeholders...")
        
        from documents.utils import extract_placeholders_from_docx  # Move import here
        
        extract_placeholders_from_docx(instance)





class GeneratedDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the user
    file = models.FileField(upload_to='documents/')  # Store document files
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp

    def __str__(self):
        return f"{self.user.username} - {self.file.name}"

class SubmittedDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submitted_documents")
    template = models.ForeignKey('documents.DocumentTemplate', on_delete=models.CASCADE, related_name="submitted_documents")
    document = models.FileField(upload_to='submitted_documents/')  # Temporary null allowed
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ], default='Pending')
    submitted_at = models.DateTimeField(auto_now_add=True)

    rejection_reason = models.TextField(blank=True, null=True) # Store rejection reason

    def __str__(self):
         return f"Submission {self.id} by {self.user.username} ({self.status})"


class ApprovedDocument(models.Model):
    original_submission = models.OneToOneField(
        'SubmittedDocument', 
        on_delete=models.CASCADE,
        related_name='approved_version'
    )
    signed_file = models.FileField(upload_to='approved_docs/')
    approved_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_docs'
    )

    def __str__(self):
        return f"Approved version of {self.original_submission}"

    class Meta:
        verbose_name = "Approved Document"
        verbose_name_plural = "Approved Documents"

