from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import timedelta
import uuid

from libraryapp.models import Book, Borrow, Review

User = get_user_model()


class BookModelTest(TestCase):
    """Test cases for Book model"""

    def setUp(self):
        """Set up test user and book"""
        self.user = User.objects.create_user(
            email="author@example.com",
            password="testpass123"
        )

    def test_book_creation(self):
        """Test creating a book with valid data"""
        book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            description="Test Description",
            file="test_file.pdf",
            uploaded_by=self.user,
        )
        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.author, "Test Author")
        self.assertTrue(book.is_active)
        self.assertIsNotNone(book.created_at)

    def test_book_id_is_uuid(self):
        """Test that book ID is a UUID"""
        book = Book.objects.create(
            title="UUID Test",
            author="Author",
            file="file.pdf",
            uploaded_by=self.user,
        )
        self.assertIsInstance(book.id, uuid.UUID)

    def test_book_summary_blank_by_default(self):
        """Test that summary is blank when not provided"""
        book = Book.objects.create(
            title="Book",
            author="Author",
            file="file.pdf",
            uploaded_by=self.user,
        )
        self.assertEqual(book.summary, "")

    def test_book_sentiment_score_nullable(self):
        """Test that sentiment_score is nullable"""
        book = Book.objects.create(
            title="Book",
            author="Author",
            file="file.pdf",
            uploaded_by=self.user,
        )
        self.assertIsNone(book.sentiment_score)

    def test_book_uploaded_by_required(self):
        """Test that uploaded_by is required"""
        with self.assertRaises(ValueError):
            Book.objects.create(
                title="Book",
                author="Author",
                file="file.pdf",
            )

    def test_book_update(self):
        """Test updating a book"""
        book = Book.objects.create(
            title="Original",
            author="Author",
            file="file.pdf",
            uploaded_by=self.user,
        )
        book.title = "Updated"
        book.save()
        
        refreshed_book = Book.objects.get(id=book.id)
        self.assertEqual(refreshed_book.title, "Updated")

    def test_book_deletion_cascade(self):
        """Test that deleting user deletes their books"""
        book = Book.objects.create(
            title="Book",
            author="Author",
            file="file.pdf",
            uploaded_by=self.user,
        )
        book_id = book.id
        self.user.delete()
        
        with self.assertRaises(Book.DoesNotExist):
            Book.objects.get(id=book_id)


class BorrowModelTest(TestCase):
    """Test cases for Borrow model"""

    def setUp(self):
        """Set up test users and book"""
        self.author = User.objects.create_user(
            email="author@example.com",
            password="testpass123"
        )
        self.borrower = User.objects.create_user(
            email="borrower@example.com",
            password="testpass123"
        )
        self.book = Book.objects.create(
            title="Book",
            author="Author",
            file="file.pdf",
            uploaded_by=self.author,
        )

    def test_borrow_creation(self):
        """Test creating a borrow"""
        expires_at = timezone.now() + timedelta(days=7)
        borrow = Borrow.objects.create(
            user=self.borrower,
            book=self.book,
            expires_at=expires_at,
        )
        self.assertEqual(borrow.user, self.borrower)
        self.assertEqual(borrow.book, self.book)
        self.assertTrue(borrow.is_active)
        self.assertIsNone(borrow.returned_at)

    def test_borrow_id_is_uuid(self):
        """Test that borrow ID is a UUID"""
        expires_at = timezone.now() + timedelta(days=7)
        borrow = Borrow.objects.create(
            user=self.borrower,
            book=self.book,
            expires_at=expires_at,
        )
        self.assertIsInstance(borrow.id, uuid.UUID)

    def test_borrow_return_book(self):
        """Test returning a borrowed book"""
        expires_at = timezone.now() + timedelta(days=7)
        borrow = Borrow.objects.create(
            user=self.borrower,
            book=self.book,
            expires_at=expires_at,
        )
        borrow.is_active = False
        borrow.returned_at = timezone.now()
        borrow.save()
        
        refreshed_borrow = Borrow.objects.get(id=borrow.id)
        self.assertFalse(refreshed_borrow.is_active)
        self.assertIsNotNone(refreshed_borrow.returned_at)

    def test_unique_active_borrow_constraint(self):
        """Test that constraint prevents multiple active borrows of same book"""
        expires_at = timezone.now() + timedelta(days=7)
        Borrow.objects.create(
            user=self.borrower,
            book=self.book,
            expires_at=expires_at,
        )
        
        # Try to create another active borrow for same user and book
        with self.assertRaises(Exception):
            Borrow.objects.create(
                user=self.borrower,
                book=self.book,
                expires_at=expires_at,
            )

    def test_borrow_deletion_cascade(self):
        """Test that deleting book deletes its borrows"""
        expires_at = timezone.now() + timedelta(days=7)
        borrow = Borrow.objects.create(
            user=self.borrower,
            book=self.book,
            expires_at=expires_at,
        )
        borrow_id = borrow.id
        self.book.delete()
        
        with self.assertRaises(Borrow.DoesNotExist):
            Borrow.objects.get(id=borrow_id)


class ReviewModelTest(TestCase):
    """Test cases for Review model"""

    def setUp(self):
        """Set up test users and book"""
        self.author = User.objects.create_user(
            email="author@example.com",
            password="testpass123"
        )
        self.reviewer = User.objects.create_user(
            email="reviewer@example.com",
            password="testpass123"
        )
        self.book = Book.objects.create(
            title="Book",
            author="Author",
            file="file.pdf",
            uploaded_by=self.author,
        )

    def test_review_creation(self):
        """Test creating a review"""
        review = Review.objects.create(
            user=self.reviewer,
            book=self.book,
            rating=5,
            comment="Great book!",
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Great book!")
        self.assertEqual(review.user, self.reviewer)
        self.assertEqual(review.book, self.book)

    def test_review_id_is_uuid(self):
        """Test that review ID is a UUID"""
        review = Review.objects.create(
            user=self.reviewer,
            book=self.book,
            rating=4,
            comment="Good",
        )
        self.assertIsInstance(review.id, uuid.UUID)

    def test_review_with_min_rating(self):
        """Test creating a review with rating 1"""
        review = Review.objects.create(
            user=self.reviewer,
            book=self.book,
            rating=1,
            comment="Not good",
        )
        self.assertEqual(review.rating, 1)

    def test_review_with_max_rating(self):
        """Test creating a review with rating 5"""
        review = Review.objects.create(
            user=self.reviewer,
            book=self.book,
            rating=5,
            comment="Excellent",
        )
        self.assertEqual(review.rating, 5)

    def test_review_deletion_cascade(self):
        """Test that deleting book deletes its reviews"""
        review = Review.objects.create(
            user=self.reviewer,
            book=self.book,
            rating=4,
            comment="Good",
        )
        review_id = review.id
        self.book.delete()
        
        with self.assertRaises(Review.DoesNotExist):
            Review.objects.get(id=review_id)

    def test_multiple_reviews_per_book(self):
        """Test that a book can have multiple reviews"""
        reviewer2 = User.objects.create_user(
            email="reviewer2@example.com",
            password="testpass123"
        )
        review1 = Review.objects.create(
            user=self.reviewer,
            book=self.book,
            rating=5,
            comment="Great",
        )
        review2 = Review.objects.create(
            user=reviewer2,
            book=self.book,
            rating=3,
            comment="Okay",
        )
        
        reviews = Review.objects.filter(book=self.book)
        self.assertEqual(reviews.count(), 2)
