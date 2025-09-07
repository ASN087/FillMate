from django import forms
from .models import UserProfile
from django.core.exceptions import ValidationError



def validate_signature_file(value):
    if value.size > 2*1024*1024:  # 2MB max
        raise ValidationError("File too large (max 2MB)")
    if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise ValidationError("Only PNG or JPG files allowed")
    # Make sure to return the value if validation passes!
    return value # <-- IMPORTANT: Add this return if missing

class SignatureUploadForm(forms.ModelForm):

    # ✅✅ ENSURE THIS META CLASS IS PRESENT AND CORRECT ✅✅
    class Meta:
        model = UserProfile  # <--- THIS LINE IS CRUCIAL
        fields = ['digital_signature']
        widgets = {
            'digital_signature': forms.FileInput(attrs={
                'accept': 'image/png, image/jpeg, image/jpg', # Added jpg just in case
                'class': 'form-control' # Assuming you use Bootstrap or similar
            })
        }
    # ✅✅ END OF META CLASS CHECK ✅✅

    # Your cleaning method (leave as is, but check the validator call)
    def clean_digital_signature(self):
        data = self.cleaned_data.get('digital_signature') # Use .get() for safety

        # Check if a file was actually uploaded before validating
        if data:
            # Call the validator function correctly
            validate_signature_file(data) # This raises ValidationError if invalid
        else:
            # Handle case where signature is optional or being cleared
            # If signature is required, ModelForm usually handles this,
            # but you might add: raise ValidationError("Signature is required.")
            pass # Allow empty if blank=True, null=True on model

        return data # Always return the cleaned data