from rest_framework import serializers

from .models import Book


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

