from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
from unittest.mock import patch, MagicMock

from libraryapp.models import Book, Borrow, Review
from libraryapp.services import BookService, BorrowService, ReviewService

User = get_user_model()


class BookServiceTest(TestCase):
    """Test cases for BookService"""

    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            email="author@example.com",
            password="testpass123"
        )

    def test_save_book_success(self):
        """Test successfully saving a book"""
        service = BookService()
        file = SimpleUploadedFile("test.pdf", b"file content")
        
        book = service.save_book(
            user=self.user,
            title="Test Book",
            author="Test Author",
            description="Test Description",
            file=file,
        )
        
        self.assertIsNotNone(book.id)
        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.author, "Test Author")
        self.assertEqual(book.uploaded_by, self.user)

    def test_save_book_creates_object(self):
        """Test that save_book creates a book in the database"""
        service = BookService()
        file = SimpleUploadedFile("test.pdf", b"file content")
        
        book = service.save_book(
            user=self.user,
            title="DB Test",
            author="Author",
            description="Description",
            file=file,
        )
        
        # Verify book exists in database
        db_book = Book.objects.get(id=book.id)
        self.assertEqual(db_book.title, "DB Test")

    @patch('libraryapp.services.extract_text')
    @patch('libraryapp.services.get_llm_client')
    def test_generate_summary_success(self, mock_llm, mock_extract):
        """Test generating a summary for a book"""
        mock_extract.return_value = "Sample text content"
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_summary.return_value = "This is a summary"
        mock_llm.return_value = mock_llm_instance
        
        service = BookService()
        file = SimpleUploadedFile("test.pdf", b"file content")
        
        book = service.save_book(
            user=self.user,
            title="Book",
            author="Author",
            description="Description",
            file=file,
        )
        
        with patch('libraryapp.services.chunk_text', return_value=["chunk1", "chunk2"]):
            service.generate_summary(str(book.id))
        
        book.refresh_from_db()
        self.assertIsNotNone(book.summary)
        self.assertEqual(book.summary, "This is a summary")

    @patch('libraryapp.services.extract_text')
    @patch('libraryapp.services.get_llm_client')
    def test_generate_summary_skips_if_exists(self, mock_llm, mock_extract):
        """Test that generate_summary skips if summary already exists"""
        service = BookService()
        file = SimpleUploadedFile("test.pdf", b"file content")
        
        book = service.save_book(
            user=self.user,
            title="Book",
            author="Author",
            description="Description",
            file=file,
        )
        
        book.summary = "Existing summary"
        book.save()
        
        service.generate_summary(str(book.id))
        
        # Verify extract_text was not called (summary already exists)
        mock_extract.assert_not_called()

    def test_generate_summary_nonexistent_book(self):
        """Test generate_summary with nonexistent book"""
        service = BookService()
        
        with self.assertRaises(Book.DoesNotExist):
            service.generate_summary("nonexistent-id")


class BorrowServiceTest(TestCase):
    """Test cases for BorrowService"""

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
        self.service = BorrowService()

    def test_borrow_book_success(self):
        """Test successfully borrowing a book"""
        borrow = self.service.borrow_book(
            user=self.borrower,
            book_id=str(self.book.id),
        )
        
        self.assertEqual(borrow.user, self.borrower)
        self.assertEqual(borrow.book, self.book)
        self.assertTrue(borrow.is_active)
        self.assertIsNone(borrow.returned_at)

    def test_borrow_book_sets_expiry(self):
        """Test that borrow sets correct expiry date"""
        borrow = self.service.borrow_book(
            user=self.borrower,
            book_id=str(self.book.id),
        )
        
        expected_expires = timezone.now() + timedelta(days=7)
        # Allow 1 minute difference due to timing
        time_diff = abs((borrow.expires_at - expected_expires).total_seconds())
        self.assertLess(time_diff, 60)

    def test_borrow_nonexistent_book(self):
        """Test borrowing a nonexistent book"""
        with self.assertRaises(ValidationError):
            self.service.borrow_book(
                user=self.borrower,
                book_id="nonexistent-id",
            )

    def test_borrow_inactive_book(self):
        """Test borrowing an inactive book"""
        self.book.is_active = False
        self.book.save()
        
        with self.assertRaises(ValidationError):
            self.service.borrow_book(
                user=self.borrower,
                book_id=str(self.book.id),
            )

    def test_author_cannot_borrow_own_book(self):
        """Test that author cannot borrow their own book"""
        with self.assertRaises(ValidationError) as context:
            self.service.borrow_book(
                user=self.author,
                book_id=str(self.book.id),
            )
        self.assertIn("cannot borrow your own book", str(context.exception))

    def test_duplicate_active_borrow_prevented(self):
        """Test that duplicate active borrow is prevented"""
        self.service.borrow_book(
            user=self.borrower,
            book_id=str(self.book.id),
        )
        
        with self.assertRaises(ValidationError) as context:
            self.service.borrow_book(
                user=self.borrower,
                book_id=str(self.book.id),
            )
        self.assertIn("already have an active borrow", str(context.exception))

    def test_return_book_success(self):
        """Test successfully returning a book"""
        borrow = self.service.borrow_book(
            user=self.borrower,
            book_id=str(self.book.id),
        )
        
        returned = self.service.return_book(
            user=self.borrower,
            book_id=str(self.book.id),
        )
        
        self.assertFalse(returned.is_active)
        self.assertIsNotNone(returned.returned_at)

    def test_return_nonexistent_borrow(self):
        """Test returning a book that wasn't borrowed"""
        with self.assertRaises(ValidationError) as context:
            self.service.return_book(
                user=self.borrower,
                book_id=str(self.book.id),
            )
        self.assertIn("No active borrow found", str(context.exception))

    def test_return_book_resets_expiry(self):
        """Test that returning book doesn't affect others"""
        borrower2 = User.objects.create_user(
            email="borrower2@example.com",
            password="testpass123"
        )
        
        borrow1 = self.service.borrow_book(
            user=self.borrower,
            book_id=str(self.book.id),
        )
        self.service.return_book(user=self.borrower, book_id=str(self.book.id))
        
        # Second borrower should be able to borrow
        borrow2 = self.service.borrow_book(
            user=borrower2,
            book_id=str(self.book.id),
        )
        
        self.assertTrue(borrow2.is_active)


class ReviewServiceTest(TestCase):
    """Test cases for ReviewService"""

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
        self.service = ReviewService()

    def test_create_review_success(self):
        """Test successfully creating a review"""
        # First borrow the book
        from libraryapp.services import BorrowService
        borrow_service = BorrowService()
        borrow_service.borrow_book(user=self.reviewer, book_id=str(self.book.id))
        
        review = self.service.create_review(
            user=self.reviewer,
            book_id=str(self.book.id),
            rating=5,
            comment="Great book!",
        )
        
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Great book!")
        self.assertEqual(review.user, self.reviewer)

    def test_review_nonexistent_book(self):
        """Test reviewing a nonexistent book"""
        with self.assertRaises(ValidationError):
            self.service.create_review(
                user=self.reviewer,
                book_id="nonexistent-id",
                rating=5,
                comment="Comment",
            )

    def test_author_cannot_review_own_book(self):
        """Test that author cannot review their own book"""
        with self.assertRaises(ValidationError) as context:
            self.service.create_review(
                user=self.author,
                book_id=str(self.book.id),
                rating=5,
                comment="Comment",
            )
        self.assertIn("cannot review your own book", str(context.exception))

    def test_review_requires_borrow(self):
        """Test that review requires prior borrow"""
        with self.assertRaises(ValidationError):
            self.service.create_review(
                user=self.reviewer,
                book_id=str(self.book.id),
                rating=5,
                comment="Comment",
            )
