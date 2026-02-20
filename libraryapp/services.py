from django.contrib.auth import get_user_model
from django.db import transaction

from libraryapp.models import Book


class BookService:

    def save_book(
        self,
        *,
        user,
        title: str,
        author: str,
        description: str,
        file,
    ) -> Book:
        """
        Create and persist a new book.
        Does NOT trigger async jobs.
        """

        book = Book.objects.create(
            title=title,
            author=author,
            description=description,
            file=file,
            uploaded_by=user,
        )

        return book

    def generate_summary(self, book_id: str):
        """
        Generate summary for a book.
        This will be called from Celery.
        """

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return

        # Prevent duplicate processing
        if book.summary:
            return

        # ---- Stub logic for now ----
        # Later: extract file text and call LLM
        book.summary = "Summary generation in progress..."
        book.save(update_fields=["summary"])
