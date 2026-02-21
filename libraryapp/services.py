import logging

from django.contrib.auth import get_user_model
from django.db import transaction

from libraryapp.models import Book
from lib.llm.factory import get_llm_client
from lib.llm.token_utils import chunk_text
from lib.extraction.utils import extract_text

logger = logging.getLogger(__name__)


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
        logger.info(f"Saving book '{title}' by '{author}' for user '{user.username}'")
        book = Book.objects.create(
            title=title,
            author=author,
            description=description,
            file=file,
            uploaded_by=user,
        )

        return book

    
    def generate_summary(self, book_id: str):
        logger.info(f"Summary generation for book ID {book_id} started...")
        book = Book.objects.get(id=book_id)
        if book.summary:
            logger.info(f"Summary already exists for book ID {book_id}")
            return

        raw_text = extract_text(book.file.path)

        llm = get_llm_client()
        summaries = []
        for chunk in chunk_text(raw_text, max_tokens=20000):
            summary = llm.generate_summary(chunk)
            summaries.append(summary)

        combined_text = "\n\n".join(summaries)
        final_summary = llm.generate_summary(combined_text)

        book.summary = final_summary
        book.save(update_fields=["summary"])
