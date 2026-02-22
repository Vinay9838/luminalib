import logging

from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from lib.llm.factory import get_llm_client
from lib.llm.token_utils import chunk_text
from lib.extraction.utils import extract_text
from libraryapp.models import Book, Borrow, Review
from libraryapp.task_service import TaskService


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
        TaskService.update_progress(10, 100)
        book = Book.objects.get(id=book_id)
        if book.summary:
            logger.info(f"Summary already exists for book ID {book_id}")
            return

        raw_text = extract_text(book.file.path, TaskService.update_progress)

        llm = get_llm_client()
        summaries = []
        current_progress = 30
        for chunk in chunk_text(raw_text, max_tokens=20000):
            current_progress += 10  # Simulate progress increase for each chunk
            if current_progress > 80:
                current_progress += 1  # Slow down progress as we approach the end
            TaskService.update_progress(current_progress, 100)  # Progress update for each chunk
            summary = llm.generate_summary(chunk)
            summaries.append(summary)

        combined_text = "\n\n".join(summaries)
        final_summary = llm.generate_summary(combined_text)
        TaskService.update_progress(100, 100)  # Final progress update

        book.summary = final_summary
        book.save(update_fields=["summary"])


class BorrowService:

    BORROW_DURATION_DAYS = 7

    def borrow_book(self, *, user, book_id):

        try:
            book = Book.objects.get(id=book_id, is_active=True)
        except Book.DoesNotExist:
            raise ValidationError("Book not found.")

        # Author cannot borrow own book
        if book.uploaded_by == user:
            raise ValidationError("You cannot borrow your own book.")

        # Prevent duplicate active borrow
        existing = Borrow.objects.filter(
            user=user,
            book=book,
            is_active=True,
            expires_at__gt=timezone.now()
        ).exists()

        if existing:
            raise ValidationError(
                "You already have an active borrow for this book."
            )

        expires_at = timezone.now() + timedelta(
            days=self.BORROW_DURATION_DAYS
        )

        borrow = Borrow.objects.create(
            user=user,
            book=book,
            expires_at=expires_at,
        )

        return borrow
    
    def return_book(self, *, user, book_id):

        try:
            borrow = Borrow.objects.get(
                user=user,
                book_id=book_id,
                is_active=True,
            )
        except Borrow.DoesNotExist:
            raise ValidationError(
                "No active borrow found for this book."
            )

        borrow.is_active = False
        borrow.returned_at = timezone.now()
        borrow.save(update_fields=["is_active", "returned_at"])

        return borrow
    

class ReviewService:

    def create_review(self, *, user, book_id, rating, comment):

        try:
            book = Book.objects.get(id=book_id, is_active=True)
        except Book.DoesNotExist:
            raise ValidationError("Book not found.")

        if book.uploaded_by == user:
            raise ValidationError(
                "You cannot review your own book."
            )

        has_borrowed = Borrow.objects.filter(
            user=user,
            book=book
        ).exists()

        if not has_borrowed:
            raise ValidationError(
                "You can only review books you have borrowed."
            )

        review = Review.objects.create(
            user=user,
            book=book,
            rating=rating,
            comment=comment,
        )

        return review
    
    def generate_sentiment(self, review_id: str):

        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return

        if not review.comment:
            return

        if review.sentiment_score is not None:
            return  # prevent duplicate processing
        
        llm = get_llm_client()
        sentiment = llm.analyze_sentiment(review.comment)

        review.sentiment_score = sentiment
        review.save(update_fields=["sentiment_score"])

    def generate_review_consensus(self, book_id: str):

        try:
            book = Book.objects.get(id=book_id, is_active=True)
        except Book.DoesNotExist:
            return

        reviews = Review.objects.filter(book=book)

        if not reviews.exists():
            book.review_consensus = ""
            book.review_consensus_updated_at = timezone.now()
            book.save(update_fields=["review_consensus", "review_consensus_updated_at"])
            return

        review_texts = [
            f"Rating: {r.rating}. Comment: {r.comment}"
            for r in reviews if r.comment
        ]

        if not review_texts:
            return

        combined_reviews = "\n".join(review_texts)

        llm = get_llm_client()
        consensus = llm.generate_review_consensus(combined_reviews)

        book.review_consensus = consensus
        book.review_consensus_updated_at = timezone.now()
        book.save(update_fields=["review_consensus", "review_consensus_updated_at"])
