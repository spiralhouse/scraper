# Scraper

[![Python Tests](https://github.com/johnburbridge/scraper/actions/workflows/python-package.yml/badge.svg)](https://github.com/johnburbridge/scraper/actions/workflows/python-package.yml)
[![Coverage](https://codecov.io/gh/johnburbridge/scraper/branch/main/graph/badge.svg)](https://codecov.io/gh/johnburbridge/scraper)

## Objectives
* Given a URL, recursively crawl its links
  * Store the response
  * Parse the response extracting new links
  * Visit each link and repeat the operations above
* Cache the results to avoid duplicative requests
* Optionally, specify the maximum recursion depth
* Optionally, specify whether to allow requests to other subdomains or domains
* Optimize the process to leverage all available processors

## Design

### 1. Architecture Components

The project will be structured with these core components:

1. **Crawler** - Main component that orchestrates the crawling process
2. **RequestHandler** - Handles HTTP requests with proper headers, retries, and timeouts
3. **ResponseParser** - Parses HTML responses to extract links
4. **Cache** - Stores visited URLs and their responses
5. **LinkFilter** - Filters links based on domain/subdomain rules
6. **TaskManager** - Manages parallel execution of crawling tasks

### 2. Caching Strategy

For the caching requirement:

- **In-memory cache**: Fast but limited by available RAM
- **File-based cache**: Persistent but slower
- **Database cache**: Structured and persistent, but requires setup

We'll start with a simple in-memory cache using Python's built-in `dict` for development, then expand to a persistent solution like SQLite for production use.

### 3. Concurrency Model

For optimizing to leverage all available processors:

- **Threading**: Good for I/O bound operations like web requests
- **Multiprocessing**: Better for CPU-bound tasks
- **Async I/O**: Excellent for many concurrent I/O operations

We'll use `asyncio` with `aiohttp` for making concurrent requests, as web scraping is primarily I/O bound.

### 4. URL Handling and Filtering

For domain/subdomain filtering:
- Use `urllib.parse` to extract and compare domains
- Implement a configurable rule system (allow/deny lists)
- Handle relative URLs properly by converting them to absolute

### 5. Depth Management

For recursion depth:
- Track depth as a parameter passed to each recursive call
- Implement a max depth check before proceeding with crawling
- Consider breadth-first vs. depth-first strategies

### 6. Error Handling & Politeness

Additional considerations:
- Robust error handling for network issues and malformed HTML
- Rate limiting to avoid overwhelming servers
- Respect for `robots.txt` rules
- User-agent identification

### 7. Data Storage

For storing the crawled data:
- Define a clear structure for storing URLs and their associated content
- Consider what metadata to keep (status code, headers, timestamps)

## User Guide

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/scraper.git
cd scraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage

To start crawling a website:

```bash
python main.py https://example.com
```

This will crawl the website with default settings (depth of 3, respecting robots.txt, not following external links).

### Command Line Options

The scraper supports the following command-line arguments:

| Option | Description |
|--------|-------------|
| `url` | The URL to start crawling from (required) |
| `-h, --help` | Show help message and exit |
| `-d, --depth DEPTH` | Maximum recursion depth (default: 3) |
| `--allow-external` | Allow crawling external domains |
| `--no-subdomains` | Disallow crawling subdomains |
| `-c, --concurrency CONCURRENCY` | Maximum concurrent requests (default: 10) |
| `--no-cache` | Disable caching |
| `--cache-dir CACHE_DIR` | Directory for cache storage |
| `--delay DELAY` | Delay between requests in seconds (default: 0.1) |
| `-v, --verbose` | Enable verbose logging |
| `--output-dir OUTPUT_DIR` | Directory to save results as JSON files |
| `--print-pages` | Print scraped pages to console |
| `--ignore-robots` | Ignore robots.txt rules |
| `--use-sitemap` | Use sitemap.xml for URL discovery |
| `--max-subsitemaps MAX_SUBSITEMAPS` | Maximum number of sub-sitemaps to process (default: 5) |
| `--sitemap-timeout SITEMAP_TIMEOUT` | Timeout in seconds for sitemap processing (default: 30) |

### Examples

#### Crawl with a specific depth limit:
```bash
python main.py https://example.com --depth 5
```

#### Allow crawling external domains:
```bash
python main.py https://example.com --allow-external
```

#### Save crawled pages to a specific directory:
```bash
python main.py https://example.com --output-dir results
```

#### Use sitemap for discovery with a longer timeout:
```bash
python main.py https://example.com --use-sitemap --sitemap-timeout 60
```

#### Maximum performance for a large site:
```bash
python main.py https://example.com --depth 4 --concurrency 20 --ignore-robots
```

#### Crawl site slowly to avoid rate limiting:
```bash
python main.py https://example.com --delay 1.0
```

## Testing

The project includes a local testing environment based on Docker that generates a controlled website structure for development and testing purposes.

### Test Environment Features

- 400+ HTML pages in a hierarchical structure
- Maximum depth of 5 levels
- Navigation links between pages at different levels
- Proper `robots.txt` and `sitemap.xml` files
- Random metadata on pages for testing extraction

### Setting Up the Test Environment

1. Make sure Docker and Docker Compose are installed and running.

2. Generate the test site (if not already done):
```bash
./venv/bin/python generate_test_site.py
```

3. Start the Nginx server:
```bash
docker-compose up -d
```

4. The test site will be available at http://localhost:8080

### Running Tests Against the Test Environment

#### Basic crawl:
```bash
python main.py http://localhost:8080 --depth 2
```

#### Test with sitemap parsing:
```bash
python main.py http://localhost:8080 --use-sitemap
```

#### Test robots.txt handling:
```bash
# Default behavior respects robots.txt
python main.py http://localhost:8080 --depth 4 

# Ignore robots.txt to crawl all pages
python main.py http://localhost:8080 --depth 4 --ignore-robots
```

#### Save the crawled results:
```bash
python main.py http://localhost:8080 --output-dir test_results
```

### Stopping the Test Environment

To stop the Docker container:
```bash
docker-compose down
```

### Regenerating the Test Site

If you need to regenerate the test site with different characteristics, modify the configuration variables at the top of the `generate_test_site.py` file and run:

```bash
./venv/bin/python generate_test_site.py
```

For more details on the test environment, see the [README-test-environment.md](README-test-environment.md) file.
