# Development Guide

[← Back to README](../README.md)

This guide provides instructions for setting up a development environment, running tests, and contributing to the scraper project.

## Setting Up a Development Environment

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for integration testing)
- Git

### Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/spiralhouse/scraper.git
cd scraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
pip install -r requirements.txt
```

## Running Tests

### Unit Tests

To run all unit tests:
```bash
pytest
```

To run tests with coverage reporting:
```bash
pytest --cov=scraper --cov-report=term-missing
```

To run a specific test file:
```bash
pytest tests/test_crawler.py
```

### Integration Tests

The project includes a Docker-based test environment that generates a controlled website for testing.

1. Generate the test site:
```bash
python generate_test_site.py
```

2. Start the test environment:
```bash
docker-compose up -d
```

3. Run the scraper against the test site:
```bash
python main.py http://localhost:8080 --depth 2
```

4. Stop the test environment when done:
```bash
docker-compose down
```

### Alternative Test Server

If Docker is unavailable, you can use the Python-based test server:

```bash
python serve_test_site.py
```

This will start a local HTTP server on port 8080 serving the same test site.

## Code Quality Tools

### Linting

To check code quality with flake8:
```bash
flake8 scraper tests
```

### Type Checking

To run type checking with mypy:
```bash
mypy scraper
```

### Code Formatting

To format code with black:
```bash
black scraper tests
```

## Debugging

### Verbose Output

To enable verbose logging:
```bash
python main.py https://example.com -v
```

### Profiling

To profile the crawler's performance:
```bash
python -m cProfile -o crawler.prof main.py https://example.com --depth 1
python -c "import pstats; p = pstats.Stats('crawler.prof'); p.sort_stats('cumtime').print_stats(30)"
```

## Test Coverage

Current test coverage is monitored through CI and displayed as a badge in the README. To increase coverage:

1. Check current coverage gaps:
```bash
pytest --cov=scraper --cov-report=term-missing
```

2. Target untested functions or code paths with new tests
3. Verify coverage improvement after adding tests

## Project Structure

```
scraper/                 # Main package directory
├── __init__.py          # Package initialization
├── cache_manager.py     # Cache implementation
├── callbacks.py         # Callback functions for crawled pages
├── crawler.py           # Main crawler class
├── request_handler.py   # HTTP request/response handling
├── response_parser.py   # HTML parsing and link extraction
├── robots_parser.py     # robots.txt parsing and checking
└── sitemap_parser.py    # sitemap.xml parsing

tests/                   # Test suite
├── __init__.py
├── conftest.py          # pytest fixtures
├── test_cache.py        # Tests for cache_manager.py
├── test_crawler.py      # Tests for crawler.py
├── test_request_handler.py
├── test_response_parser.py
├── test_robots_parser.py
└── test_sitemap_parser.py

docs/                    # Documentation
├── project.md           # Project overview and features
└── develop.md           # Development guide

.github/workflows/       # CI configuration
```

## Contributing

### Pull Request Process

1. Create a new branch for your feature or bugfix
2. Implement your changes with appropriate tests
3. Ensure all tests pass and coverage doesn't decrease
4. Submit a pull request with a clear description of the changes

### Coding Standards

- Follow PEP 8 style guidelines
- Include docstrings for all functions, classes, and modules
- Add type hints to function signatures
- Keep functions focused on a single responsibility
- Write tests for all new functionality 