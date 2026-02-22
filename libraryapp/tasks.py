from celery import shared_task
from libraryapp.services import BookService, ReviewService


@shared_task
def generate_book_summary_task(book_id: str):
    try:
        BookService().generate_summary(book_id)
    except Exception:
        raise


@shared_task
def generate_review_sentiment_task(review_id: str, book_id: str):
    try:
        review_svc = ReviewService()
        review_svc.generate_sentiment(review_id)
        review_svc.generate_review_consensus(book_id)
    except Exception:
        raise
