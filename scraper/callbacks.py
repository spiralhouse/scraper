"""
Callback functions that can be used with the Crawler.

This module provides example callback functions that can be passed to
the Crawler's on_page_crawled parameter to customize crawling behavior.
"""

import json
import os
from typing import Dict, Any


def console_printer(url: str, page_data: Dict[str, Any]) -> None:
    """
    Print page information to the console.
    
    Args:
        url: The URL that was crawled
        page_data: Data about the crawled page
    """
    print(f"\n--- Page Crawled: {url} ---")
    print(f"Title: {page_data.get('title', 'No title')}")
    print(f"Status: {page_data.get('status_code', 0)}")
    print(f"Depth: {page_data.get('depth', 0)}")
    print(f"Links found: {len(page_data.get('links', []))}")
    print("-" * 50)


def json_file_writer(output_dir: str) -> callable:
    """
    Create a callback function that writes page data to JSON files.
    
    Args:
        output_dir: Directory where JSON files will be saved
        
    Returns:
        Callback function that can be passed to Crawler
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    def callback(url: str, page_data: Dict[str, Any]) -> None:
        """
        Write page data to a JSON file.
        
        Args:
            url: The URL that was crawled
            page_data: Data about the crawled page
        """
        # Create a safe filename from URL
        safe_filename = url.replace("://", "_").replace("/", "_").replace(".", "_")
        if len(safe_filename) > 100:
            safe_filename = safe_filename[:100]  # Truncate long filenames
            
        # Create full path
        file_path = os.path.join(output_dir, f"{safe_filename}.json")
        
        # Write data to file
        with open(file_path, 'w') as f:
            json.dump(page_data, f, indent=2)
    
    return callback
    

def link_collector(collected_links: set) -> callable:
    """
    Create a callback function that collects links into a provided set.
    
    Args:
        collected_links: Set where links will be stored
        
    Returns:
        Callback function that can be passed to Crawler
    """
    def callback(url: str, page_data: Dict[str, Any]) -> None:
        """
        Add links from the page to the collected_links set.
        
        Args:
            url: The URL that was crawled
            page_data: Data about the crawled page
        """
        links = page_data.get('links', [])
        collected_links.update(links)
    
    return callback 