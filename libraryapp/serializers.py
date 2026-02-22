from rest_framework import serializers

from .models import Book, Borrow, Review


class BookUploadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        fields = ["title", "author", "description", "file"]

    def validate_file(self, value):
        allowed_extensions = ["pdf", "txt"]
        ext = value.name.split(".")[-1].lower()

        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                "Only PDF and TXT files are allowed."
            )

        return value
    
class BookListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "description",
            "summary",
            "created_at",
        ]


class BookDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "description",
            "summary",
            "sentiment_score",
            "created_at",
            "updated_at",
        ]


class BookUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        fields = ["title", "author", "description"]

    def validate(self, attrs):
        request = self.context["request"]
        book = self.instance

        if book.uploaded_by != request.user:
            raise serializers.ValidationError(
                "You are not allowed to update this book."
            )

        return attrs
    

class BorrowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrow
        fields = [
            "id",
            "book",
            "borrowed_at",
            "expires_at",
        ]


class ReviewCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = ["rating", "comment"]

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value
    

class RequestStatusSerializer(serializers.Serializer):
    request_id = serializers.CharField()
    request_status = serializers.CharField()
    request_progress = serializers.FloatField()


class BookAnalysisSerializer(serializers.Serializer):
    book_id = serializers.UUIDField()
    average_rating = serializers.FloatField(allow_null=True)
    total_reviews = serializers.IntegerField()
    review_consensus = serializers.CharField(allow_blank=True)
    consensus_last_updated = serializers.DateTimeField(allow_null=True)
