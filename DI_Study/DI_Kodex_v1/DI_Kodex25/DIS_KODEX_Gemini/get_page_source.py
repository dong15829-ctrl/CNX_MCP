import requests
from bs4 import BeautifulSoup

# The original URL redirects, so we start there.
# Using a common user-agent to mimic a browser.
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# The initial URL that redirects
url = "https://www.tigeretf.com/"

try:
    # Allow redirects to get the final URL
    response = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
    response.raise_for_status()  # Raise an exception for bad status codes

    # Get the final URL after redirects
    final_url = response.url
    print(f"Initial URL: {url}")
    print(f"Final URL after redirect: {final_url}")

    # Use BeautifulSoup to parse and prettify the HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    pretty_html = soup.prettify()

    # Save the prettified HTML to a file for inspection
    file_path = "debug_tiger_page.html"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(pretty_html)

    print(f"Successfully downloaded and saved HTML to {file_path}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

