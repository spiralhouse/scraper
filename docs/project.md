# Scraper Project Overview

[← Back to README](../README.md)

## Objectives
* Given a URL, recursively crawl its links
  * Store the response
  * Parse the response extracting new links
  * Visit each link and repeat the operations above
* Cache the results to avoid duplicative requests
* Optionally, specify the maximum recursion depth
* Optionally, specify whether to allow requests to other subdomains or domains
* Optimize the process to leverage all available processors

## Architecture Components

The project is structured with these core components:

1. **Crawler** - Main component that orchestrates the crawling process
2. **RequestHandler** - Handles HTTP requests with proper headers, retries, and timeouts
3. **ResponseParser** - Parses HTML responses to extract links
4. **Cache** - Stores visited URLs and their responses
5. **LinkFilter** - Filters links based on domain/subdomain rules
6. **SitemapParser** - Extracts URLs from site's sitemap.xml
7. **RobotsParser** - Interprets and follows robots.txt directives
8. **Callbacks** - Processes crawled pages (console output, JSON files, etc.)

## Caching Strategy

The scraper implements a persistent SQLite-based cache:

- **Schema**: Stores URLs, content, headers, status codes, and timestamps
- **Expiry**: Configurable TTL for cache entries
- **Performance**: Fast lookups and efficient storage
- **Disk-based**: Persists between runs for incremental crawling

## Concurrency Model

For optimizing to leverage all available processors:

- **Async I/O**: Uses `asyncio` for many concurrent I/O operations
- **Task Management**: Dynamic task creation and limiting
- **Rate Limiting**: Configurable delay between requests
- **Resource Control**: Respects system limitations

## URL Handling and Filtering

For domain/subdomain filtering:
- **Domain Isolation**: Restricts crawling to the target domain by default
- **Subdomain Control**: Configurable inclusion/exclusion of subdomains
- **URL Normalization**: Resolves relative URLs to absolute paths
- **URL Filtering**: Skips binary files and unwanted file types

## Depth Management

For recursion depth:
- **Level Tracking**: Maintains depth of each page in the crawl
- **Depth Limiting**: Stops at configured maximum depth
- **Breadth-First Approach**: Ensures thorough coverage at each level

## Politeness Features

Implements web crawler etiquette:
- **Robots.txt Support**: Respects website crawler policies
- **Rate Limiting**: Configurable delay between requests
- **Proper User-Agent**: Identifies itself appropriately
- **Sitemap Usage**: Can use the site's sitemap.xml for discovery
- **Error Handling**: Backs off on server errors

## Data Processing

Flexible options for handling crawled data:
- **Console Output**: Displays crawled pages in terminal
- **JSON Storage**: Saves pages as structured data files
- **Custom Callbacks**: Extensible system for custom processing
- **Statistics**: Provides detailed crawl statistics 