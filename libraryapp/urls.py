from django.urls import path

from .views import BookUploadView

app_name = 'libraryapp'
urlpatterns = [
    path('upload/', BookUploadView.as_view(), name='book-upload'),
]