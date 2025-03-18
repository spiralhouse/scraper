#!/usr/bin/env python3
import argparse
import logging
import sys
import os
from typing import Dict, Any

from scraper.crawler import Crawler
from scraper.callbacks import console_printer, json_file_writer, link_collector


def configure_logging(verbose: bool) -> None:
    """
    Configure logging based on verbosity level.
    
    Args:
        verbose: Whether to enable verbose logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def print_stats(stats: Dict[str, Any]) -> None:
    """
    Print crawling statistics in a pretty format.
    
    Args:
        stats: Dictionary of stats from the crawler
    """
    print("\n===== Crawling Statistics =====")
    print(f"Pages Crawled: {stats['pages_crawled']}")
    print(f"Pages Skipped (from cache): {stats['pages_skipped']}")
    print(f"Total URLs Visited: {stats['total_urls']}")
    
    # Print sitemap stats if available
    if "sitemap_urls_found" in stats:
        print(f"Sitemap URLs Found: {stats['sitemap_urls_found']}")
        print(f"Sitemap URLs Used: {stats['sitemap_urls_used']}")
    
    print(f"Duration: {stats['duration']:.2f} seconds")
    print("==============================\n")


def main() -> int:
    """
    Main entry point for the scraper.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(description="Web crawler that recursively follows links from a starting URL")
    
    parser.add_argument("url", help="The URL to start crawling from")
    parser.add_argument("-d", "--depth", type=int, default=3, help="Maximum recursion depth (default: 3)")
    parser.add_argument("--allow-external", action="store_true", help="Allow crawling external domains")
    parser.add_argument("--no-subdomains", action="store_true", help="Disallow crawling subdomains")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="Maximum concurrent requests (default: 10)")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    parser.add_argument("--cache-dir", help="Directory for cache storage")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between requests in seconds (default: 0.1)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--output-dir", help="Directory to save results as JSON files")
    parser.add_argument("--print-pages", action="store_true", help="Print scraped pages to console")
    parser.add_argument("--ignore-robots", action="store_true", help="Ignore robots.txt rules")
    parser.add_argument("--use-sitemap", action="store_true", help="Use sitemap.xml for URL discovery")
    parser.add_argument("--max-subsitemaps", type=int, default=5, help="Maximum number of sub-sitemaps to process (default: 5)")
    parser.add_argument("--sitemap-timeout", type=int, default=30, help="Timeout in seconds for sitemap processing (default: 30)")
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logging(args.verbose)
    
    # Set up callbacks
    callback = None
    
    if args.print_pages and args.output_dir:
        # Both console printing and JSON output
        all_links = set()
        json_cb = json_file_writer(args.output_dir)
        link_cb = link_collector(all_links)
        
        def combined_callback(url, data):
            console_printer(url, data)
            json_cb(url, data)
            link_cb(url, data)
            
        callback = combined_callback
    elif args.print_pages:
        # Just console printing
        callback = console_printer
    elif args.output_dir:
        # Just JSON output
        callback = json_file_writer(args.output_dir)
    
    # Create crawler instance
    crawler = Crawler(
        max_depth=args.depth,
        allow_external_domains=args.allow_external,
        allow_subdomains=not args.no_subdomains,
        concurrency_limit=args.concurrency,
        use_cache=not args.no_cache,
        cache_dir=args.cache_dir,
        request_delay=args.delay,
        on_page_crawled=callback,
        respect_robots_txt=not args.ignore_robots,
        use_sitemap=args.use_sitemap,
        max_subsitemaps=args.max_subsitemaps,
        sitemap_timeout=args.sitemap_timeout
    )
    
    try:
        # Start crawling
        print(f"Starting crawl from {args.url} with max depth {args.depth}")
        stats = crawler.crawl(args.url)
        
        # Print stats
        print_stats(stats)
        
        return 0
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user.")
        return 130
    except Exception as e:
        logging.error(f"Error during crawling: {str(e)}")
        return 1
    finally:
        crawler.close()


if __name__ == "__main__":
    sys.exit(main())
