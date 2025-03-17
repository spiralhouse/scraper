#!/usr/bin/env python
import os
import random
import xml.dom.minidom
from datetime import datetime, timedelta

# Configuration
NUM_TOP_LEVEL_PAGES = 8
NUM_SECTIONS = 6  # Number of section directories
PAGES_PER_SECTION = 7  # Pages per section
MAX_DEPTH = 5  # Maximum depth of page hierarchy
SITE_DOMAIN = "http://localhost:8080"  # Domain for sitemap

# Create directories
os.makedirs("example-site", exist_ok=True)
for i in range(1, NUM_SECTIONS + 1):
    os.makedirs(f"example-site/section{i}", exist_ok=True)
    
# Track all pages for sitemap and robots
all_pages = []
disallowed_pages = []

def create_navigation(current_page, depth=0):
    """Create navigation links for a page."""
    nav_links = [
        f'<li><a href="/">Home</a></li>'
    ]
    
    # Add links to top-level pages
    for i in range(1, NUM_TOP_LEVEL_PAGES + 1):
        page_name = f"page{i}.html"
        if current_page != page_name:
            nav_links.append(f'<li><a href="/{page_name}">Page {i}</a></li>')
    
    # Add links to sections
    for i in range(1, NUM_SECTIONS + 1):
        section = f"section{i}"
        nav_links.append(f'<li><a href="/{section}/">Section {i}</a></li>')
    
    return f"""
    <nav>
        <ul>{''.join(nav_links)}</ul>
    </nav>
    """

def create_content(page_name, depth=0, section=None):
    """Create content with links based on depth and section."""
    links = []
    
    # Add links based on depth
    if depth < MAX_DEPTH:
        # Create "child" pages (deeper hierarchy)
        child_pages = random.randint(1, 3)  # Random number of child pages
        for i in range(1, child_pages + 1):
            child_name = f"subpage{i}.html"
            path_prefix = f"{section}/" if section else ""
            
            # Build the correct path based on current page's location
            if page_name == "index.html":
                link_path = f"{path_prefix}{child_name}"
            elif page_name.startswith("subpage"):
                # For subpages, append depth information to distinguish them
                dirname = os.path.dirname(f"depth{depth+1}_{child_name}")
                if dirname:
                    os.makedirs(f"example-site/{path_prefix}{dirname}", exist_ok=True)
                link_path = f"{path_prefix}depth{depth+1}_{child_name}"
            else:
                # For regular pages, create subpages in their "directory"
                dir_name = page_name.replace(".html", "")
                os.makedirs(f"example-site/{path_prefix}{dir_name}", exist_ok=True)
                link_path = f"{path_prefix}{dir_name}/{child_name}"
                
            links.append(f'<li><a href="/{link_path}">Child page {i} (depth {depth+1})</a></li>')
            
            # Add the child page to all pages list
            all_pages.append(f"/{link_path}")
            
            # Create the child page recursively
            create_page(link_path, depth + 1, section)
    
    # Add some cross-section links on higher level pages
    if depth <= 1 and random.random() < 0.7:
        other_section = random.randint(1, NUM_SECTIONS)
        section_page = random.randint(1, PAGES_PER_SECTION)
        links.append(f'<li><a href="/section{other_section}/page{section_page}.html">Random link to Section {other_section}</a></li>')
    
    # Create content with links
    content = f"""
    <h1>{section if section else "Main"} - {'Index' if page_name == 'index.html' else page_name.replace('.html', '')}</h1>
    <p>This is a test page at depth {depth}.</p>
    
    <div class="metadata">
        <p>Page ID: {random.randint(10000, 99999)}</p>
        <p>Last Updated: {(datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')}</p>
        <p>Category: {'Section ' + section.replace('section', '') if section else 'Main'}</p>
    </div>
    
    {'<h2>Subpages</h2><ul>' + ''.join(links) + '</ul>' if links else '<p>No subpages available.</p>'}
    
    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, 
    nisl eget ultricies tincidunt, nisl nisl aliquet nisl, eget aliquet nisl 
    nisl eget nisl. Nullam auctor, nisl eget ultricies tincidunt.</p>
    """
    return content

def create_page(page_path, depth=0, section=None):
    """Create an HTML page at the given path."""
    is_section_index = page_path.endswith("/")
    
    if is_section_index:
        page_path = page_path + "index.html"
        
    # Determine actual filesystem path
    file_path = os.path.join("example-site", page_path)
    
    # Create parent directory if needed
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Extract the page name for navigation
    page_name = os.path.basename(page_path)
    
    # Randomly disallow some deep pages from robots.txt
    if depth >= 3 and random.random() < 0.3:
        disallowed_pages.append(f"/{page_path}")
    
    # Create HTML content
    navigation = create_navigation(page_name, depth)
    content = create_content(page_name, depth, section)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{'Section ' + section.replace('section', '') if section else 'Main'} - {page_name.replace('.html', '')}</title>
    <meta name="description" content="Test page for web crawler - Depth {depth}">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        nav {{ background-color: #f4f4f4; padding: 10px; margin-bottom: 20px; }}
        nav ul {{ list-style: none; padding: 0; display: flex; flex-wrap: wrap; }}
        nav li {{ margin-right: 15px; }}
        .metadata {{ background-color: #efefef; padding: 10px; margin: 20px 0; }}
        footer {{ margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px; }}
    </style>
</head>
<body>
    <header>
        {navigation}
    </header>
    <main>
        {content}
    </main>
    <footer>
        <p>Test Site for Web Crawler - Page depth: {depth}</p>
    </footer>
</body>
</html>"""
    
    # Write the HTML file
    with open(file_path, "w") as f:
        f.write(html)
    
    return f"/{page_path}"

# Create homepage
print("Generating homepage...")
homepage_path = create_page("index.html")
all_pages.append(homepage_path)

# Create top-level pages
print("Generating top-level pages...")
for i in range(1, NUM_TOP_LEVEL_PAGES + 1):
    page_path = create_page(f"page{i}.html")
    all_pages.append(page_path)

# Create sections with pages
print("Generating section pages...")
for section_num in range(1, NUM_SECTIONS + 1):
    section = f"section{section_num}"
    
    # Create section index
    section_index_path = create_page(f"{section}/", 0, section)
    all_pages.append(section_index_path)
    
    # Create section pages
    for page_num in range(1, PAGES_PER_SECTION + 1):
        page_path = create_page(f"{section}/page{page_num}.html", 1, section)
        all_pages.append(page_path)

# Create robots.txt
print("Generating robots.txt...")
robots_content = """User-agent: *
Crawl-delay: 0.1

"""
for disallowed in disallowed_pages:
    robots_content += f"Disallow: {disallowed}\n"

with open("example-site/robots.txt", "w") as f:
    f.write(robots_content)

# Create sitemap.xml
print("Generating sitemap.xml...")
doc = xml.dom.minidom.getDOMImplementation().createDocument(None, "urlset", None)
root = doc.documentElement
root.setAttribute("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

for page in all_pages:
    if page not in disallowed_pages:  # Don't include disallowed pages in sitemap
        url_elem = doc.createElement("url")
        
        loc = doc.createElement("loc")
        loc_text = doc.createTextNode(f"{SITE_DOMAIN}{page}")
        loc.appendChild(loc_text)
        url_elem.appendChild(loc)
        
        # Add lastmod with random date
        lastmod = doc.createElement("lastmod")
        date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
        lastmod_text = doc.createTextNode(date)
        lastmod.appendChild(lastmod_text)
        url_elem.appendChild(lastmod)
        
        # Add changefreq
        changefreq = doc.createElement("changefreq")
        freq_options = ["daily", "weekly", "monthly"]
        freq = random.choice(freq_options)
        changefreq_text = doc.createTextNode(freq)
        changefreq.appendChild(changefreq_text)
        url_elem.appendChild(changefreq)
        
        # Add priority
        priority = doc.createElement("priority")
        # Higher level pages get higher priority
        if page.count('/') <= 2:
            pri = 0.8
        else:
            pri = 0.5
        priority_text = doc.createTextNode(f"{pri:.1f}")
        priority.appendChild(priority_text)
        url_elem.appendChild(priority)
        
        root.appendChild(url_elem)

with open("example-site/sitemap.xml", "w") as f:
    f.write(doc.toprettyxml())
    
# Print summary
print(f"Generated {len(all_pages)} pages")
print(f"Disallowed {len(disallowed_pages)} pages from robots.txt")
print("Done!") 