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
