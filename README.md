# LuminaLib

LuminaLib is a modular library and web application for managing, extracting, and analyzing book data using advanced extraction techniques and LLM (Large Language Model) integrations. It is built with Django, Celery, and supports extensible extractors for PDF and text files, as well as LLM clients for AI-powered features.

## Features

- Book data extraction from PDFs and text files
- LLM integration (Azure, Ollama, etc.) for advanced processing
- REST API for library and user management
- Celery-based background task processing
- Modular architecture for easy extension
- JWT-based authentication

## Project Structure

```
luminalib/
├── data/                # Book data storage
├── lib/                 # Core extraction and LLM logic
│   ├── extraction/      # Extractors for PDF, text, etc.
│   └── llm/             # LLM client integrations
├── libraryapp/          # Django app for library management
├── userapp/             # Django app for user management
├── luminalib/           # Django project settings and celery config
├── scripts/             # Utility scripts
├── Dockerfile           # Docker support
├── docker-compose.yml   # Docker Compose setup
├── manage.py            # Django management
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Setup

### Prerequisites
- Python 3.8+
- Docker & Docker Compose (optional, for containerized setup)

### Local Development
1. **Clone the repository:**
	```bash
	git clone <repo-url>
	cd luminalib
	```
2. **Create and activate a virtual environment:**
	```bash
	python3 -m venv .venv
	source .venv/bin/activate
	```
3. **Install dependencies:**
	```bash
	pip install -r requirements.txt
	```
4. **Apply migrations:**
	```bash
	python manage.py migrate
	```
5. **Run the development server:**
	```bash
	python manage.py runserver
	```

### Using Docker
1. **Build and start services:**
	```bash
	docker-compose up --build
	```

## Usage

- Access the web app at `http://localhost:8000/`
- API endpoints are available under `/api/`
- Use the admin interface at `/admin/` (create a superuser with `python manage.py createsuperuser`)

## Background Tasks

Celery is used for background processing. To start the worker:

```bash
celery -A luminalib worker --loglevel=info
```

## Testing

Run tests with:

```bash
python manage.py test
```

## Extending Extractors or LLM Clients

- Add new extractors in `lib/extraction/`
- Add new LLM clients in `lib/llm/`

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push to your branch and open a Pull Request

## License

MIT License

---
For more details, see the code and comments in each module.
