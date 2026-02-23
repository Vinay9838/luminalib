from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import uuid

from libraryapp.models import Book, Borrow, Review

User = get_user_model()


class BookUploadViewTest(APITestCase):
    """Test cases for BookUploadView"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="author@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    @patch('libraryapp.views.generate_book_summary_task.delay')
    def test_upload_book_success(self, mock_task):
        """Test successfully uploading a book"""
        mock_task.return_value = MagicMock(id="task-id-123")
        
        file = SimpleUploadedFile("test.pdf", b"file content")
        data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'description': 'Test Description',
            'file': file,
        }
        
        response = self.client.post('/api/books/upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('book', response.data)
        self.assertIn('request_id', response.data)

    def test_upload_book_without_authentication(self):
        """Test uploading without authentication"""
        self.client.force_authenticate(user=None)
        
        file = SimpleUploadedFile("test.pdf", b"content")
        data = {
            'title': 'Book',
            'author': 'Author',
            'description': 'Description',
            'file': file,
        }
        
        response = self.client.post('/api/books/upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_book_unsupported_format(self):
        """Test uploading unsupported file format"""
        file = SimpleUploadedFile("test.doc", b"content")
        data = {
            'title': 'Book',
            'author': 'Author',
            'description': 'Description',
            'file': file,
        }
        
        response = self.client.post('/api/books/upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('libraryapp.views.generate_book_summary_task.delay')
    def test_upload_book_creates_database_entry(self, mock_task):
        """Test that upload creates a book in database"""
        mock_task.return_value = MagicMock(id="task-id")
        
        file = SimpleUploadedFile("test.pdf", b"content")
        data = {
            'title': 'DB Test Book',
            'author': 'Author',
            'description': 'Description',
            'file': file,
        }
        
        self.client.post('/api/books/upload/', data, format='multipart')
        
        book = Book.objects.get(title='DB Test Book')
        self.assertEqual(book.author, 'Author')
        self.assertEqual(book.uploaded_by, self.user)


class BookListViewTest(APITestCase):
    """Test cases for BookListView"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="author@example.com",
            password="testpass123"
        )
        self.book1 = Book.objects.create(
            title="Book 1",
            author="Author 1",
            file="file1.pdf",
            uploaded_by=self.user,
        )
        self.book2 = Book.objects.create(
            title="Book 2",
            author="Author 2",
            file="file2.pdf",
            uploaded_by=self.user,
        )

    def test_list_books_success(self):
        """Test listing books"""
        response = self.client.get('/api/books/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_books_filters_by_author(self):
        """Test filtering books by author"""
        response = self.client.get('/api/books/?author=Author 1')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['author'], 'Author 1')

    def test_list_books_filters_by_title(self):
        """Test filtering books by title"""
        response = self.client.get('/api/books/?title=Book 2')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Book 2')

    def test_list_books_excludes_inactive(self):
        """Test that inactive books are excluded"""
        self.book1.is_active = False
        self.book1.save()
        
        response = self.client.get('/api/books/')
        
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Book 2')

    def test_list_books_pagination(self):
        """Test that book list is paginated"""
        response = self.client.get('/api/books/')
        
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)


class BookDetailViewTest(APITestCase):
    """Test cases for BookDetailView"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="author@example.com",
            password="testpass123"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            description="Description",
            file="file.pdf",
            uploaded_by=self.user,
            summary="Test summary",
        )

    def test_get_book_detail(self):
        """Test getting book detail"""
        response = self.client.get(f'/api/books/{self.book.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Book')
        self.assertEqual(response.data['summary'], 'Test summary')

    def test_get_nonexistent_book(self):
        """Test getting nonexistent book"""
        fake_id = uuid.uuid4()
        response = self.client.get(f'/api/books/{fake_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_inactive_book(self):
        """Test getting inactive book returns 404"""
        self.book.is_active = False
        self.book.save()
        
        response = self.client.get(f'/api/books/{self.book.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BookUpdateViewTest(APITestCase):
    """Test cases for BookUpdateView"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.author = User.objects.create_user(
            email="author@example.com",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123"
        )
        self.book = Book.objects.create(
            title="Original Title",
            author="Original Author",
            file="file.pdf",
            uploaded_by=self.author,
        )

    def test_update_book_as_author(self):
        """Test updating book as author"""
        self.client.force_authenticate(user=self.author)
        
        data = {
            'title': 'Updated Title',
            'author': 'Updated Author',
            'description': 'Updated Description',
        }
        
        response = self.client.put(f'/api/books/{self.book.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, 'Updated Title')

    def test_update_book_as_other_user(self):
        """Test updating book as non-author fails"""
        self.client.force_authenticate(user=self.other_user)
        
        data = {
            'title': 'Updated Title',
            'author': 'Author',
            'description': 'Description',
        }
        
        response = self.client.put(f'/api/books/{self.book.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BorrowViewTest(APITestCase):
    """Test cases for Borrow endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
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
        self.client.force_authenticate(user=self.borrower)

    def test_borrow_book_success(self):
        """Test borrowing a book"""
        data = {'book_id': str(self.book.id)}
        
        response = self.client.post('/api/borrow/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Borrow.objects.filter(
            user=self.borrower,
            book=self.book
        ).exists())

    def test_borrow_without_authentication(self):
        """Test borrowing without authentication"""
        self.client.force_authenticate(user=None)
        
        data = {'book_id': str(self.book.id)}
        response = self.client.post('/api/borrow/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReviewViewTest(APITestCase):
    """Test cases for Review endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
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
        # Reviewer borrows the book first
        from libraryapp.services import BorrowService
        service = BorrowService()
        service.borrow_book(user=self.reviewer, book_id=str(self.book.id))
        
        self.client.force_authenticate(user=self.reviewer)

    def test_create_review_success(self):
        """Test creating a review"""
        data = {
            'book_id': str(self.book.id),
            'rating': 5,
            'comment': 'Great book!',
        }
        
        response = self.client.post('/api/reviews/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Review.objects.filter(
            user=self.reviewer,
            book=self.book
        ).exists())

    def test_create_review_without_authentication(self):
        """Test creating review without authentication"""
        self.client.force_authenticate(user=None)
        
        data = {
            'book_id': str(self.book.id),
            'rating': 5,
            'comment': 'Great!',
        }
        
        response = self.client.post('/api/reviews/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
