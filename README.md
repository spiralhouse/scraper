# Scraper

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
