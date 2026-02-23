# LuminaLib Architecture

This document explains the architectural design decisions, background job processing, and LLM extensibility in LuminaLib.

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [System Architecture](#system-architecture)
3. [Background Job Processing](#background-job-processing)
4. [LLM Abstraction & Swapping](#llm-abstraction--swapping)
5. [Extractor Abstraction](#extractor-abstraction)
6. [Database Design](#database-design)
7. [API Design](#api-design)

---

## Design Philosophy

### Goals

LuminaLib was designed with the following principles:

1. **Modularity** - Core functionality is separated into pluggable modules
2. **Extensibility** - New extractors, LLM providers, and services can be added without modifying existing code
3. **Async Processing** - Long-running operations don't block API responses
4. **Scalability** - Distributed task processing and independent components
5. **Type Safety** - Abstract base classes enforce contracts for implementations

### Why These Decisions?

#### 1. **Factory Pattern for Extractors & LLM Clients**

Rather than hardcoding PDF or Azure LLM clients, we use the **Factory Pattern**:

```python
# Instead of tight coupling:
from lib.llm.azure_client import AzureClient
llm = AzureClient()  # Hard to swap

# We use a factory:
from lib.llm.factory import get_llm_client
llm = get_llm_client()  # Easy to configure
```

**Benefits:**
- Configuration-driven selection (environment variables)
- No code changes needed to switch providers
- Easy testing with mocks
- Clear separation of concerns

#### 2. **Abstract Base Classes**

Both `BaseExtractor` and `BaseLLM` are abstract base classes:

```python
class BaseLLM(ABC):
    @abstractmethod
    def generate_summary(self, text: str) -> str:
        pass

    @abstractmethod
    def analyze_sentiment(self, text: str) -> float:
        pass
```

**Benefits:**
- Enforces consistent interface across implementations
- IDE support for implementing new providers
- Runtime errors if contract not fulfilled
- Clear documentation of required methods

#### 3. **Celery for Background Processing**

Book summaries and reviews are processed asynchronously via Celery:

```python
# Async processing
task = generate_book_summary_task.delay(str(book.id))
return Response({'request_id': task.id})  # Return immediately
```

**Benefits:**
- API responds instantly (better UX)
- Long-running tasks don't timeout
- Tasks can be retried on failure
- Progress tracking via TaskService
- Multiple workers can process in parallel

#### 4. **Service Layer Pattern**

Business logic is separated into service classes (`BookService`, `BorrowService`, `ReviewService`):

```python
# Clean separation of concerns
class BookService:
    def save_book(self, **kwargs) -> Book:
        # Core business logic
        pass

    def generate_summary(self, book_id: str):
        # Complex summary generation
        pass
```

**Benefits:**
- Reusable across API views, tasks, and CLI commands
- Easier unit testing
- Clear business logic flow
- Easy to add validation and error handling

---

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Client (Web/Mobile)                  │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│            Django REST API                              │
│  ┌──────────────────┬──────────────────┬────────────┐   │
│  │  BookViews      │  BorrowViews    │ ReviewViews │   │
│  └────────┬─────────┴────────┬────────┴────────┬────┘   │
│           │                  │                 │        │
│           ▼                  ▼                 ▼        │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Service Layer                            │   │
│  │  ┌────────────┬──────────────┬──────────────┐    │   │
│  │  │BookService │BorrowService │ReviewService │    │   │
│  │  └────────────┴──────────────┴──────────────┘    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                           │
                ┌──────────┼──────────┐
                ▼          ▼          ▼
         ┌──────────┐ ┌────────┐ ┌─────────────┐
         │ Database │ │ Celery │ │ LLM Service │
         │(Models)  │ │(Tasks) │ │(Abstractions)
         └──────────┘ └────────┘ └─────────────┘
                │          │           │
                │    ┌─────┴─────┐     │
                │    ▼           ▼     ▼
                │   Redis    ┌─────────────────┐
                │           │  LLM Providers   │
                │           │  ┌─────────────┐ │
                ▼           │  │ Azure/Ollama│ │
              PostgreSQL    │  │ /Custom     │ │
                            │  └─────────────┘ │
                            └─────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---|
| **Views (REST API)** | Handle HTTP requests, authentication, serialization |
| **Services** | Contain business logic, validation, orchestration |
| **Models** | Database schema, relationships, ORM definitions |
| **Celery Tasks** | Background job execution, progress tracking |
| **Extractors** | Text extraction from PDF, TXT files |
| **LLM Clients** | API integration with language models |
| **Database** | Persistent storage of books, borrows, reviews |
| **Redis** | Message broker for Celery, caching |

---

## Background Job Processing

### Why Async Processing?

**Problem:** Generating summaries from large PDFs can take 30+ seconds

```
❌ Synchronous (Bad):
User Request → Extract Text → Call LLM → Generate Summary → Return Response
            (30+ seconds blocking)
            User experiences timeout or long wait
```

```
✅ Asynchronous (Good):
User Request → Queue Task → Return Immediately with Job ID
                    ↓ (runs in background)
             Worker Process → Extract → LLM → Save to DB
            (user can check progress)
```

### Implementation Flow

#### 1. **API View Queues Task**

```python
# libraryapp/views.py
@extend_schema(summary="Upload a new book")
def post(self, request):
    serializer = BookUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    service = BookService()
    book = service.save_book(
        user=request.user,
        **serializer.validated_data,
    )
    
    # Queue async task
    task = generate_book_summary_task.delay(str(book.id))
    
    return Response(
        {'book': BookUploadSerializer(book).data, 'request_id': task.id},
        status=status.HTTP_201_CREATED,
    )
```

**Returns immediately with task ID so client can check progress.**

#### 2. **Celery Task Executes**

```python
# libraryapp/tasks.py
@shared_task
def generate_book_summary_task(book_id: str):
    """
    Async task to generate book summary.
    Runs in background Celery worker.
    """
    try:
        service = BookService()
        service.generate_summary(book_id)
    except Exception as exc:
        # Task will be retried automatically
        raise self.retry(exc=exc, countdown=60)
```

#### 3. **Service Method Does Heavy Lifting**

```python
# libraryapp/services.py
def generate_summary(self, book_id: str):
    """Complex summary generation with progress tracking."""
    logger.info(f"Summary generation for book ID {book_id} started...")
    TaskService.update_progress(10, 100)
    
    book = Book.objects.get(id=book_id)
    raw_text = extract_text(book.file.path, TaskService.update_progress)
    
    llm = get_llm_client()
    summaries = []
    
    for chunk in chunk_text(raw_text, max_tokens=20000):
        TaskService.update_progress(current_progress, 100)
        summary = llm.generate_summary(chunk)
        summaries.append(summary)
    
    combined_text = "\n\n".join(summaries)
    final_summary = llm.generate_summary(combined_text)
    
    book.summary = final_summary
    book.save(update_fields=["summary"])
```

#### 4. **Client Polls for Status**

```bash
# Get job status
GET /api/request-status/{request_id}/

Response:
{
    "status": "IN_PROGRESS",
    "progress": 45,
    "total": 100
}

# When complete
{
    "status": "COMPLETED",
    "progress": 100,
    "total": 100,
    "result": { "book": {...} }
}
```

### Task Execution Flow Diagram

```
┌─────────────┐
│ Client      │
└──────┬──────┘
       │ POST /books/upload/
       ▼
┌──────────────────────────┐
│ BookUploadView           │
│ 1. Save book to DB       │
│ 2. Queue task with ID    │
│ 3. Return task ID        │
└──────┬───────────────────┘
       │ (returns immediately)
       ▼
┌──────────────────────────┐
│ Celery Redis Queue       │
│ Task: generate_summary   │
│ Book ID: abc-123         │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Celery Worker            │
│ 1. Extract text (10s)    │
│ 2. Chunk text (5s)       │
│ 3. Generate summaries    │
│    via LLM (15s)         │
│ 4. Save to DB (1s)       │
└──────┬───────────────────┘
       │ (Total: ~31s)
       ▼
┌──────────────────────────┐
│ Database                 │
│ Updated book.summary     │
└──────────────────────────┘
```

### Configuration

**docker-compose.yml**
```yaml
celery:
  build: .
  command: celery -A luminalib worker --loglevel=info
  depends_on:
    - redis
    - db

redis:
  image: redis:latest
  ports:
    - "6379:6379"
```

**settings.py**
```python
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEOUT = 3600  # Tasks timeout after 1 hour
```

### Failure Handling

```python
@shared_task(bind=True, max_retries=3)
def generate_book_summary_task(self, book_id: str):
    try:
        service = BookService()
        service.generate_summary(book_id)
    except Exception as exc:
        # Exponential backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

---

## LLM Abstraction & Swapping

### Why Abstraction?

LLM providers have different APIs and capabilities:

- **Azure OpenAI** - Expensive, powerful, requires API key
- **Ollama** - Free, local, requires model download
- **Custom** - In-house models, proprietary

Rather than hardcoding one provider, we **abstract the interface**:

```python
# Same code works with any LLM
llm = get_llm_client()  # Could be Azure, Ollama, or anything
summary = llm.generate_summary(text)  # Same method regardless
```

### Abstract Base Class

```python
# lib/llm/base.py
class BaseLLM(ABC):
    
    @abstractmethod
    def generate_summary(self, text: str) -> str:
        """Generate summary of given text."""
        pass

    @abstractmethod
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment, return score 0.0 to 1.0."""
        pass
```

All implementations **must** provide these methods.

### Implementation Example: Azure Client

```python
# lib/llm/azure_client.py
class AzureClient(BaseLLM):
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_API_KEY,
            endpoint=settings.AZURE_ENDPOINT,
            api_version="2024-02-15-preview"
        )
    
    def generate_summary(self, text: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f"Summarize: {text}"}
            ]
        )
        return response.choices[0].message.content
    
    def analyze_sentiment(self, text: str) -> float:
        # Implementation...
        pass
```

### Implementation Example: Ollama Client

```python
# lib/llm/ollama_client.py
class OllamaClient(BaseLLM):
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "mistral"  # Free local model
    
    def generate_summary(self, text: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": f"Summarize: {text}",
                "stream": False
            }
        )
        return response.json()["response"]
    
    def analyze_sentiment(self, text: str) -> float:
        # Implementation...
        pass
```

### Factory Pattern

```python
# lib/llm/factory.py
def get_llm_client() -> BaseLLM:
    """Get configured LLM client based on environment."""
    llm_type = os.getenv("LLM_TYPE", "azure").lower()
    
    if llm_type == "azure":
        logger.info("Using Azure OpenAI client")
        return AzureClient()
    
    elif llm_type == "ollama":
        logger.info("Using Ollama client")
        return OllamaClient()
    
    else:
        raise ValueError(f"Unsupported LLM type: {llm_type}")
```

### Swapping Providers at Runtime

**Option 1: Environment Variable**
```bash
# Use Azure (default)
export LLM_TYPE=azure
python manage.py runserver

# Switch to Ollama
export LLM_TYPE=ollama
celery -A luminalib worker
```

**Option 2: Docker Compose**
```yaml
services:
  api:
    environment:
      LLM_TYPE: "azure"
      AZURE_API_KEY: "sk-..."
      AZURE_ENDPOINT: "https://..."

  worker:
    environment:
      LLM_TYPE: "ollama"
      OLLAMA_BASE_URL: "http://ollama:11434"
```

**Option 3: Database Configuration (Advanced)**
```python
# If you want to switch per-tenant
def get_llm_client(user=None) -> BaseLLM:
    if user and user.profile.preferred_llm:
        return get_llm_provider(user.profile.preferred_llm)
    return get_llm_client()  # Default
```

### Adding a New LLM Provider

**Step 1: Implement the interface**
```python
# lib/llm/custom_client.py
class CustomClient(BaseLLM):
    def generate_summary(self, text: str) -> str:
        # Your implementation
        pass
    
    def analyze_sentiment(self, text: str) -> float:
        # Your implementation
        pass
```

**Step 2: Register in factory**
```python
# lib/llm/factory.py
elif llm_type == "custom":
    return CustomClient()
```

**Step 3: Use it**
```bash
export LLM_TYPE=custom
python manage.py runserver
```

**That's it!** No changes needed to service layer, views, or tests.

### Token Management

For efficient LLM usage, we chunk large texts:

```python
# lib/llm/token_utils.py
def chunk_text(text: str, max_tokens: int = 20000) -> List[str]:
    """Split text into chunks respecting token limits."""
    tokens = text.split()  # Simplified; use tiktoken for production
    chunks = []
    current_chunk = []
    
    for word in tokens:
        current_chunk.append(word)
        if len(current_chunk) >= max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks
```

This prevents LLM API failures due to context window limits.

---

## Extractor Abstraction

Similar to LLM abstraction, we have pluggable extractors:

```python
# lib/extraction/base.py
class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> str:
        pass
```

### Available Extractors

| Extractor | File Type | Implementation |
|-----------|-----------|---|
| **PdfExtractor** | .pdf | Uses `pdfplumber` library |
| **TxtExtractor** | .txt | Simple file read |
| **Custom** | Any | Implement `BaseExtractor` |

### Factory Selection

```python
# lib/extraction/factory.py
def get_extractor(file_path: str) -> BaseExtractor:
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        return PdfExtractor()
    elif ext == ".txt":
        return TxtExtractor()
    else:
        raise ValueError(f"Unsupported file type: {ext}")
```

### Adding DOCX Support

```python
# lib/extraction/docx_extractor.py
from docx import Document

class DocxExtractor(BaseExtractor):
    def extract(self, file_path: str) -> str:
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
```

```python
# lib/extraction/factory.py
elif ext == ".docx":
    return DocxExtractor()
```

---

## Database Design

### Schema Overview

```
┌──────────────────────────┐
│ User                     │
│ ├── id (PK)              │
│ ├── email (UNIQUE)       │
│ ├── password_hash        │
│ └── created_at           │
└──────────┬───────────────┘
           │
           │ (uploaded_by / user)
           │
┌──────────▼──────────────────────┐
│ Book                             │
│ ├── id (UUID, PK)                │
│ ├── title                        │
│ ├── author                       │
│ ├── description                  │
│ ├── file (path)                  │
│ ├── summary (generated async)    │
│ ├── sentiment_score (nullable)   │
│ ├── uploaded_by (FK → User)      │
│ ├── is_active                    │
│ ├── created_at                   │
│ └── updated_at                   │
└──────────┬──────────────────────┘
           │
      ┌────┴──────┐
      │           │
      │ (book)    │ (book)
      ▼           ▼
┌──────────┐  ┌──────────────┐
│ Borrow   │  │ Review       │
│ ├── id   │  │ ├── id       │
│ ├── user │  │ ├── user     │
│ ├── book │  │ ├── book     │
│ └── ...  │  │ ├── rating   │
│          │  │ ├── comment  │
│          │  │ └── ...      │
└──────────┘  └──────────────┘
```

### Key Design Decisions

1. **UUID for Book ID** - Better for distributed systems, easier federation
2. **Soft Deletes (is_active)** - Don't lose data, maintain history
3. **Audit Timestamps** - Track when books were created/updated
4. **Unique Constraint on Borrow** - Prevent duplicate active borrows
5. **Cascading Deletes** - Clean up orphaned records when user/book deleted

---

## API Design

### RESTful Endpoints

```
POST   /api/books/upload/          # Upload and queue summary
GET    /api/books/                 # List all books (paginated)
GET    /api/books/{id}/            # Get book detail
PATCH  /api/books/{id}/            # Update book metadata
GET    /api/request-status/{id}/   # Check background job status

POST   /api/borrow/                # Borrow a book
POST   /api/borrow/{id}/return/    # Return book

POST   /api/reviews/               # Create review
GET    /api/reviews/               # List reviews
```

### Response Format

**Successful Upload:**
```json
{
    "book": {
        "id": "abc-123",
        "title": "Python Design Patterns",
        "author": "Gang of Four",
        "created_at": "2024-02-23T10:30:00Z"
    },
    "request_id": "task-xyz-789"
}
```

**Job Status:**
```json
{
    "status": "IN_PROGRESS",
    "progress": 65,
    "total": 100,
    "message": "Generating summary..."
}
```

### Authentication

Uses JWT tokens passed via custom header:

```
GET /api/books/ HTTP/1.1
X-JWT-Assertion: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Deosn Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Factory** | `lib/extraction/factory.py`, `lib/llm/factory.py` | Select implementations at runtime |
| **Abstract Base Class** | `BaseLLM`, `BaseExtractor` | Enforce contract, enable polymorphism |
| **Service Layer** | `BookService`, `BorrowService`, etc. | Separate business logic from HTTP |
| **Repository** | Django ORM | Abstraction over database |
| **Task Queue** | Celery | Async processing, distributed work |
| **Strategy** | LLM clients | Swap algorithms without code change |

---

## Conclusion

This architecture provides:

✅ **Flexibility** - Swap extractors and LLM providers easily  
✅ **Scalability** - Async processing with Celery workers  
✅ **Maintainability** - Clean separation of concerns  
✅ **Testability** - Mock-friendly abstractions  
✅ **Extensibility** - Add new providers without modification  

The design leverages proven patterns (Factory, Abstract Classes, Service Layer) to create a flexible, maintainable system that can adapt to changing requirements.
