from django.urls import path
from .views import DocumentTemplateListCreateView, DocumentTemplateDetailView, SubmissionDetailView, DocumentReviewView
from .views import PlaceholderListView
from documents import views
from .views import my_documents, SubmitDocumentView

app_name = 'documents'

urlpatterns = [
    path('templates/', DocumentTemplateListCreateView.as_view(), name='document-templates'),
    path('templates/<int:template_id>/placeholders/', PlaceholderListView.as_view(), name='template-placeholders'),
    path('templates/<int:pk>/', DocumentTemplateDetailView.as_view(), name='document-template-detail'),
    path('templates/<int:template_id>/preview/', views.preview_template, name='preview_template'),
    path('templates/<int:template_id>/generate/', views.generate_document, name='generate_document'),
    path('my-documents/', my_documents, name='my_documents'),
    path('templates/<int:template_id>/submit/', SubmitDocumentView.as_view(), name='submit-document'),
    path('submissions/<int:submission_id>/', SubmissionDetailView.as_view(), name='submission-detail'),
    path(
        'submissions/<int:submission_id>/review/',
        DocumentReviewView.as_view(),
        name='document-review'
    ),
]