from celery import shared_task
from libraryapp.services import BookService, ReviewService


@shared_task
def generate_book_summary_task(book_id: str):
    try:
        BookService().generate_summary(book_id)
    except Exception:
        raise


@shared_task
def generate_review_sentiment_task(review_id: str):
    try:
        ReviewService().generate_sentiment(review_id)
    except Exception:
        raise
