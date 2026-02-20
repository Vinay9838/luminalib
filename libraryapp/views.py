from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema

from libraryapp.serializers import BookUploadSerializer
from libraryapp.services import BookService
from libraryapp.tasks import generate_book_summary_task


class BookUploadView(APIView):

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Upload a new book",
        tags=["Books"],
        description="Upload a PDF or TXT book. Summary is generated asynchronously.",
        request=BookUploadSerializer,
        responses={201: BookUploadSerializer},
    )
    def post(self, request):

        serializer = BookUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = BookService()

        book = service.save_book(
            user=request.user,
            **serializer.validated_data,
        )

        # Ensure Celery runs after DB commit
        transaction.on_commit(
            lambda: generate_book_summary_task.delay(str(book.id))
        )

        return Response(
            BookUploadSerializer(book).data,
            status=status.HTTP_201_CREATED,
        )
