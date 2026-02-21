from django.urls import path

from .views import BookUploadView, BookListView, BookDetailView, BookUpdateView, BookDeleteView

app_name = 'libraryapp'
urlpatterns = [
    path('upload/', BookUploadView.as_view(), name='book-upload'),
    path("books/", BookListView.as_view(), name="book-list"),
    path("books/<uuid:id>/", BookDetailView.as_view(), name="book-detail"),
    path("books/<uuid:id>/update/", BookUpdateView.as_view(), name="book-update"),
    path("books/<uuid:id>/delete/", BookDeleteView.as_view(), name="book-delete"),
]