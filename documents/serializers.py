from rest_framework import serializers
from .models import DocumentTemplate, Placeholder, SubmittedDocument
from users.serializers import UserSerializer  # Adjusted import path

class PlaceholderSerializer(serializers.ModelSerializer):
    """Serializer to return extracted placeholders with type & example"""

    class Meta:
        model = Placeholder
        fields = ['id', 'name', 'placeholder_text', 'type', 'example']  # Include type & example

class DocumentTemplateSerializer(serializers.ModelSerializer):
    """Serializer for handling document template uploads and placeholders"""
    placeholders = PlaceholderSerializer(many=True, read_only=True)  # Automatically fetch placeholders

    class Meta:
        model = DocumentTemplate
        fields = ['id', 'name', 'file', 'created_at', 'placeholders']
        depth = 1  # Ensure placeholders are included in API response

class SubmittedDocumentSerializer(serializers.ModelSerializer):
    template = DocumentTemplateSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = SubmittedDocument
        fields = ['id', 'template', 'user', 'document', 'status', 'submitted_at']

class DocumentReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('reason'):
            raise serializers.ValidationError("Reason is required for rejection")
        return data