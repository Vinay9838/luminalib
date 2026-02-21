import os
import uuid

from django.db import models
from django.conf import settings
from django.db.models import Q, F


def book_upload_path(instance, filename):
    ext = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join("books", str(instance.id), new_filename)

class Book(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    file = models.FileField(upload_to=book_upload_path)

    summary = models.TextField(blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_books"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "books"


class Borrow(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrows"
    )

    book = models.ForeignKey(
        "libraryapp.Book",
        on_delete=models.CASCADE,
        related_name="borrows"
    )

    borrowed_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "borrows"
        indexes = [
            models.Index(fields=["user", "book"]),
            models.Index(fields=["expires_at", "is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "book"],
                condition=Q(is_active=True),
                name="unique_active_borrow_per_user_book"
            ),
            models.CheckConstraint(
            condition=Q(expires_at__gt=F("borrowed_at")),
            name="expires_after_borrowed"
        ),
        ]

class Review(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    book = models.ForeignKey(
        "libraryapp.Book",
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    rating = models.PositiveSmallIntegerField()  # 1–5
    comment = models.TextField(blank=True)

    sentiment_score = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "book"],
                name="unique_review_per_user_per_book"
            ),
            models.CheckConstraint(
            condition=Q(rating__gte=1) & Q(rating__lte=5),
            name="rating_between_1_and_5"
        ),
        ]
