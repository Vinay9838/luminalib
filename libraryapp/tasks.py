from celery import shared_task
from libraryapp.services import BookService


@shared_task
def generate_book_summary_task(book_id: str):
    BookService().generate_summary(book_id)
