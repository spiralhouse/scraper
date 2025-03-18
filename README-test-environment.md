# Web Scraper Test Environment

This directory contains a complete local test environment for testing the web scraper against a controlled website with a known structure.

## Generated Test Site

A test website with the following characteristics has been generated:
- 400+ HTML pages in a hierarchical structure
- Maximum depth of 5 levels
- Navigation links between pages at different levels
- Proper `robots.txt` and `sitemap.xml` files
- Random metadata on pages for testing extraction

## Directory Structure

- `example-site/` - Contains all the generated HTML files and resources
  - `index.html` - Homepage
  - `page*.html` - Top-level pages
  - `section*/` - Section directories with their own pages
  - `robots.txt` - Contains crawler directives with some intentionally disallowed pages
  - `sitemap.xml` - XML sitemap with all publicly available pages

- `nginx/` - Contains Nginx configuration
  - `nginx.conf` - Server configuration with directory listing enabled

- `docker-compose.yml` - Docker Compose configuration for running Nginx

- `generate_test_site.py` - Script that generated the test site

## Running the Test Environment

1. Make sure Docker and Docker Compose are installed and running
2. Start the Nginx server:
   ```
   docker-compose up -d
   ```
3. The test site will be available at http://localhost:8080

## Testing the Scraper

You can test your scraper against this environment with:

```
python main.py http://localhost:8080 --depth 3
```

Additional test commands:

- Test with sitemap parsing:
  ```
  python main.py http://localhost:8080 --use-sitemap
  ```

- Test with robots.txt consideration:
  ```
  python main.py http://localhost:8080 --respect-robots-txt
  ```

## Site Characteristics for Testing

- The site contains a mix of pages that link to subpages
- Some deeper pages (depth >= 3) are disallowed in robots.txt
- Pages have consistent navigation but varying depth
- The sitemap includes all non-disallowed pages with metadata

## Regenerating the Test Site

If you need to regenerate the test site with different characteristics, modify the configuration variables at the top of the `generate_test_site.py` file and run:

```
./venv/bin/python generate_test_site.py
``` 