# Scraper

[![Python Tests](https://github.com/spiralhouse/scraper/actions/workflows/python-package.yml/badge.svg)](https://github.com/spiralhouse/scraper/actions/workflows/python-package.yml)
[![Coverage](https://codecov.io/gh/spiralhouse/scraper/branch/main/graph/badge.svg)](https://codecov.io/gh/spiralhouse/scraper)

A flexible web crawler that recursively crawls websites, respects robots.txt, and provides various output options.

## Documentation

- [Project Overview and Features](docs/project.md)
- [Development Guide](docs/develop.md)
- [Test Environment Documentation](README-test-environment.md)

## Installation

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

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Requirements

- **Python**: Compatible with Python 3.9, 3.10, 3.11, and 3.12
- All dependencies are listed in the `requirements.txt` file and are automatically installed during the installation process.
- Some optional dependencies are available for development in `requirements-dev.txt`.

## Basic Usage

To start crawling a website:

```bash
python main.py https://example.com
```

This will crawl the website with default settings (depth of 3, respecting robots.txt, not following external links).

## Command Line Options

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

## Examples

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
