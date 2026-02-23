# Test Suite Documentation

This document describes the comprehensive test suite for the LuminaLib project.

## Test Files

The test suite is organized in the `tests/` directory with the following structure:

```
tests/
├── libraryapp/
│   ├── test_models.py      # Book, Borrow, Review models
│   ├── test_services.py    # BookService, BorrowService, ReviewService
│   └── test_views.py       # REST API endpoints
├── userapp/
│   ├── test_models.py      # Custom User model
│   └── test_authentication.py  # JWT authentication
└── lib/
    ├── extraction/
    │   └── test_extractors.py  # PDF and text extractors
    └── llm/
        └── test_llm.py     # LLM clients and factory
```

### 1. **tests/libraryapp/test_models.py**
   Tests for Book, Borrow, and Review models.
   
   **BookModelTest**
   - Book creation with valid data
   - UUID primary key
   - Default values (summary, sentiment_score)
   - Required fields (uploaded_by)
   - Update operations
   - Cascade deletion

   **BorrowModelTest**
   - Borrow creation
   - Active/inactive status
   - Return book functionality
   - Unique constraint on active borrows per user-book pair
   - Cascade deletion

   **ReviewModelTest**
   - Review creation with rating and comment
   - UUID primary key
   - Rating validation (1-5)
   - Multiple reviews per book
   - Cascade deletion

### 2. **tests/libraryapp/test_services.py**
   Tests for business logic services.
   
   **BookServiceTest**
   - Save book to database
   - Generate summary from file content
   - Skip summary if already exists
   - Handle nonexistent books

   **BorrowServiceTest**
   - Successfully borrow a book
   - Validate expiry date (7 days)
   - Prevent borrowing nonexistent books
   - Prevent borrowing inactive books
   - Prevent author from borrowing own book
   - Prevent duplicate active borrow
   - Return book functionality
   - Reset borrow for other users after return

   **ReviewServiceTest**
   - Create review (requires prior borrow)
   - Prevent reviewing nonexistent book
   - Prevent author from reviewing own book
   - Require book borrow before review

### 3. **tests/userapp/test_models.py**
   Tests for custom User model.
   
   **UserModelTest**
   - User creation with email
   - Password hashing
   - Email uniqueness
   - Password verification
   - USERNAME_FIELD is email
   - Default is_staff (False) and is_active (True)
   - Superuser creation
   - User data updates

### 4. **tests/userapp/test_authentication.py**
   Tests for JWT authentication and auth service.
   
   **TokenAuthenticationTest**
   - No-token requests return None
   - Valid token authentication
   - Invalid token raises AuthenticationFailed
   - Expired token handling
   - Case-insensitive header matching

   **AuthServiceTest**
   - Get user from valid token
   - Return None for invalid token
   - Handle nonexistent user_id
   - Generate token for user
   - Verify valid and invalid tokens

### 5. **tests/lib/extraction/test_extractors.py**
   Tests for PDF and text extractors.
   
   **ExtractorFactoryTest**
   - Get PDF extractor for .pdf files
   - Get text extractor for .txt files
   - Error on unsupported file types
   - Case-insensitive extension matching

   **PdfExtractorTest**
   - Extract text from single-page PDF
   - Extract text from multi-page PDF
   - Handle empty pages
   - Progress callback invocation

   **TxtExtractorTest**
   - Extract text from text files
   - Handle multiline text
   - UTF-8 encoding support
   - Nonexistent file error handling
   - Progress callback invocation

### 6. **tests/lib/llm/test_llm.py**
   Tests for LLM client factory and base class.
   
   **LLMFactoryTest**
   - Get Azure LLM client
   - Get Ollama LLM client
   - Error on unsupported LLM type
   - Default client when LLM_TYPE not set

   **BaseLLMTest**
   - Cannot instantiate abstract base class
   - Requires generate_summary implementation
   - Requires analyze_sentiment implementation
   - Complete implementation works correctly

### 7. **tests/libraryapp/test_views.py**
   Tests for REST API endpoints.
   
   **BookUploadViewTest**
   - Upload book with valid file
   - Require authentication
   - Reject unsupported file formats
   - Create database entry

   **BookListViewTest**
   - List all active books
   - Filter by author
   - Filter by title
   - Exclude inactive books
   - Pagination

   **BookDetailViewTest**
   - Get book details
   - Handle nonexistent book
   - Exclude inactive books

   **BookUpdateViewTest**
   - Author can update book
   - Non-author cannot update book

   **BorrowViewTest**
   - Successfully borrow a book
   - Require authentication

   **ReviewViewTest**
   - Create review
   - Require authentication

## Running Tests

### Run all tests
```bash
python manage.py test tests
```

### Run tests for specific app
```bash
python manage.py test tests.libraryapp
python manage.py test tests.userapp
python manage.py test tests.lib
```

### Run specific test file
```bash
python manage.py test tests.libraryapp.test_models
python manage.py test tests.libraryapp.test_services
python manage.py test tests.libraryapp.test_views
python manage.py test tests.userapp.test_models
python manage.py test tests.userapp.test_authentication
python manage.py test tests.lib.extraction.test_extractors
python manage.py test tests.lib.llm.test_llm
```

### Run specific test class
```bash
python manage.py test tests.libraryapp.test_models.BookModelTest
python manage.py test tests.libraryapp.test_services.BookServiceTest
python manage.py test tests.userapp.test_models.UserModelTest
```

### Run specific test method
```bash
python manage.py test tests.libraryapp.test_models.BookModelTest.test_book_creation
python manage.py test tests.libraryapp.test_services.BorrowServiceTest.test_borrow_book_success
```

### Run with verbose output
```bash
python manage.py test --verbosity=2
```

### Run with coverage
```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # Creates htmlcov/index.html
```

## Test Statistics

- **Total Test Files**: 7
- **Total Test Classes**: 23
- **Total Test Methods**: 85+

## Mocking Strategy

Tests use Python's `unittest.mock` library to:
- Mock external API calls (LLM clients)
- Mock file operations
- Mock database queries where needed
- Mock Celery tasks

## Test Database

Tests use Django's test database which is:
- Created fresh for each test run
- Automatically rolled back after each test
- Isolated from production data

## Continuous Integration

To integrate with CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: python manage.py test --verbosity=2

- name: Generate coverage
  run: |
    coverage run --source='.' manage.py test
    coverage report
    coverage xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Best Practices Followed

1. **Setup/Teardown**: Each test class has setUp() for test fixtures
2. **Isolation**: Tests are independent and can run in any order
3. **Mocking**: External dependencies are mocked
4. **Assertions**: Multiple assertions verify expected behavior
5. **Edge Cases**: Tests cover success paths, errors, and edge cases
6. **Documentation**: Test names clearly describe what they test
7. **Cleanup**: Test database is automatically cleaned up

## Future Test Coverage Areas

Consider adding tests for:
- Rate limiting on APIs
- Permission checks on all endpoints
- Concurrent borrow/return operations
- Large file uploads and processing
- Background task error handling
- Email notifications (when added)
- File cleanup after upload
