import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# Constants
URL = "https://www.gaymaletube.com/search?filter%5Border_by%5D=date&filter%5Badvertiser_publish_date%5D=&filter%5Bduration%5D=1200&filter%5Bquality%5D=&filter%5Bvirtual_reality%5D=&filter%5Badvertiser_site%5D=&pricing=free"  # Replace with the actual URL
OUTPUT_DIR = "web_digests"

# Create output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def fetch_page_content(url):
    """Fetch the HTML content of the page."""
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def extract_new_items(html_content, last_known_items):
    """Extract new items from the page that are not in last_known_items."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Adjust this selector to match the structure of the page
    items = soup.select(".card")  # Replace `.item-class` with the actual CSS selector

    new_items = []
    for item in items:
        title = item.get_text(strip=True)
        link = item.get("href", "")

        if title not in last_known_items:
            new_items.append((title, link))

    return new_items

def save_digest(new_items):
    """Save the digest to a file."""
    if not new_items:
        print("No new items to save.")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    output_file = os.path.join(OUTPUT_DIR, f"digest_{date_str}.txt")

    with open(output_file, "w", encoding='utf-8') as file:
        for title, link in new_items:
            file.write(f"- {title}: {link}\n")

    print(f"Saved digest to {output_file}")

def load_last_known_items():
    """Load the titles of previously saved items."""
    all_titles = set()

    for file_name in os.listdir(OUTPUT_DIR):
        if file_name.startswith("digest_") and file_name.endswith(".txt"):
            with open(os.path.join(OUTPUT_DIR, file_name), "r") as file:
                for line in file:
                    title = line.split(":")[0].strip("- ")
                    all_titles.add(title)

    return all_titles

if __name__ == "__main__":
    print("Fetching page content...")
    html_content = fetch_page_content(URL)

    print("Loading last known items...")
    last_known_items = load_last_known_items()

    print("Extracting new items...")
    new_items = extract_new_items(html_content, last_known_items)

    print(f"Found {len(new_items)} new items.")
    save_digest(new_items)
