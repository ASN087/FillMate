from django.contrib import admin
from .models import DocumentTemplate
from .utils import extract_placeholders_from_docx
# Register your models here.

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'file', 'created_at')

    def save_model(self, request, obj, form, change):
        """Extract placeholders after saving a template from Django Admin"""
        super().save_model(request, obj, form, change)
        extract_placeholders_from_docx(obj) # Extract placeholders from the uploaded template

#admin.register(DocumentTemplate)
