# users/models.py
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone # <-- Add this import

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='userprofile' # <-- Added related_name for easier access
    )
    digital_signature = models.ImageField(
        upload_to='signatures/',
        blank=True,
        null=True, # <-- Allow null initially
        help_text="Upload a transparent PNG signature (e.g., 300x150px, max 2MB)"
    )
    # ✅ ADD THIS FIELD:
    signature_uploaded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Optional but good practice: Signal to create UserProfile when a new User is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    # If you want profile updates on user save (e.g., email change), uncomment below
    # instance.userprofile.save()