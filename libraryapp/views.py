from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Avg, Count
from rest_framework.exceptions import ValidationError as DRFValidationError


from libraryapp.models import Book, Review
from libraryapp.serializers import (
    BookUploadSerializer, 
    BookListSerializer, 
    BookDetailSerializer, 
    BookUpdateSerializer,
    BorrowSerializer,
    ReviewCreateSerializer,
    RequestStatusSerializer,
    BookAnalysisSerializer,
    BoookSerializer,
)
from libraryapp.services import BookService, BorrowService, ReviewService
from libraryapp.task_service import TaskService
from libraryapp.tasks import generate_book_summary_task, generate_review_sentiment_task


class BookUploadView(APIView):

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Upload a new book",
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

        task = generate_book_summary_task.delay(str(book.id))
        

        return Response(
            {'book': BookUploadSerializer(book).data, 'request_id': task.id},
            status=status.HTTP_201_CREATED,
        )
    

class BookListView(ListAPIView):

    serializer_class = BookListSerializer

    @extend_schema(
        summary="List all active books",
        tags=["Books"],
        description="Returns paginated list of active books. Supports filtering by author and title.",
        parameters=[
            OpenApiParameter(
                name="author",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter books by author (partial match).",
                required=False,
            ),
            OpenApiParameter(
                name="title",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter books by title (partial match).",
                required=False,
            ),
        ],
        responses=BookListSerializer(many=True),
    )
    def get_queryset(self):
        queryset = Book.objects.filter(is_active=True)

        author = self.request.query_params.get("author")
        title = self.request.query_params.get("title")

        if author:
            queryset = queryset.filter(author__icontains=author)

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.order_by("-created_at")
    

class BookDetailView(RetrieveAPIView):

    queryset = Book.objects.filter(is_active=True)
    serializer_class = BookDetailSerializer
    lookup_field = "id"

    @extend_schema(
        summary="Retrieve book details",
        description="Get detailed information of a specific book by UUID.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="UUID of the book",
                required=True,
            ),
        ],
        responses=BookDetailSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    

class BookUpdateView(UpdateAPIView):

    queryset = Book.objects.filter(is_active=True)
    serializer_class = BookUpdateSerializer
    lookup_field = "id"
    http_method_names = ["put"]

    @extend_schema(
        summary="Update a book",
        description="Only the uploader can update the book details.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="UUID of the book",
                required=True,
            ),
        ],
        request=BookUpdateSerializer,
        responses=BookDetailSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    

class BookDeleteView(APIView):

    @extend_schema(
        summary="Delete a book",
        description="Soft delete a book. Only the uploader can delete it.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="UUID of the book",
                required=True,
            ),
        ],
        responses={
            204: None,
            403: None,
            404: None,
        },
    )
    def delete(self, request, id):

        try:
            book = Book.objects.get(id=id, is_active=True)
        except Book.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if book.uploaded_by != request.user:
            raise PermissionDenied("You are not allowed to delete this book.")

        book.is_active = False
        book.save(update_fields=["is_active"])

        return Response({"message": "Book deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    

class BorrowCreateView(APIView):

    @extend_schema(
        summary="Borrow a book",
        description="Borrow a book for a fixed duration. Author cannot borrow own book.",
        request=BoookSerializer,
        responses=BorrowSerializer,
    )
    def post(self, request, id):

        service = BorrowService()

        try:
            borrow = service.borrow_book(
                user=request.user,
                book_id=id,
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message)

        return Response(
            BorrowSerializer(borrow).data,
            status=status.HTTP_201_CREATED,
        )
    

class BorrowReturnView(APIView):

    @extend_schema(
        summary="Return a borrowed book",
        description="Return a previously borrowed book. Only active borrow can be returned.",
        request=BoookSerializer,
        responses=BorrowSerializer,
    )
    def post(self, request, id):

        service = BorrowService()

        try:
            borrow = service.return_book(
                user=request.user,
                book_id=id,
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message)

        return Response(
            BorrowSerializer(borrow).data,
            status=status.HTTP_200_OK,
        )
    

class ReviewCreateView(APIView):

    @extend_schema(
        summary="Add review to a book",
        description="Only borrowers can review. Uploader cannot review own book.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="UUID of the book",
                required=True,
            ),
        ],
        request=ReviewCreateSerializer,
        responses=ReviewCreateSerializer,
    )
    def post(self, request, id):

        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ReviewService()

        try:
            review = service.create_review(
                user=request.user,
                book_id=id,
                **serializer.validated_data,
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message)

        # Trigger async sentiment generation after commit
        task = generate_review_sentiment_task.delay(str(review.id), str(review.book.id))
        

        return Response(
            {
                "request_id": task.id,
                "review": ReviewCreateSerializer(review).data,
            },
            status=status.HTTP_201_CREATED,
        )
    

class RequestProgressView(APIView):

    @extend_schema(
        summary="Check progress of an asynchronous task",
        description="Get the status and progress of a background task using its request ID.",
        parameters=[
            OpenApiParameter(
                name="request_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="UUID of the asynchronous task request",
                required=True,
            ),
        ],
        responses=RequestStatusSerializer,
    )
    def get(self, request, request_id):
        service = TaskService(request_id)
        status_str, progress = service.get_progress_info()

        return Response(
            {
                "request_id": request_id,
                "request_status": status_str,
                "request_progress": progress,
            },
            status=status.HTTP_200_OK,
        )
    
class BookAnalysisView(APIView):

    @extend_schema(
        summary="Get aggregated review analysis",
        description="Returns AI-generated consensus and review statistics for a book.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="UUID of the book",
                required=True,
            ),
        ],
        responses=BookAnalysisSerializer,
    )
    def get(self, request, id):

        try:
            book = Book.objects.get(id=id, is_active=True)
        except Book.DoesNotExist:
            raise DRFValidationError("Book not found.")

        stats = Review.objects.filter(book=book).aggregate(
            average_rating=Avg("rating"),
            total_reviews=Count("id"),
        )

        data = {
            "book_id": book.id,
            "average_rating": stats["average_rating"],
            "total_reviews": stats["total_reviews"],
            "review_consensus": book.review_consensus,
            "consensus_last_updated": book.review_consensus_updated_at,
        }

        return Response(data, status=status.HTTP_200_OK)
