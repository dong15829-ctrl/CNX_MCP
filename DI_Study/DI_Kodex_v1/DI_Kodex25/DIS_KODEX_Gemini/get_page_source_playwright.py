import asyncio
from playwright.async_api import async_playwright

async def get_final_page_source():
    """
    Uses Playwright to navigate to the product list URL and saves the page's HTML.
    """
    # The new, direct URL for the product list
    url = "https://investments.miraeasset.com/tigeretf/en/product/search/list.do"
    file_path = "debug_tiger_product_list.html"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            print(f"Navigating to {url}...")
            # Navigate to the URL and wait for the page to be fully loaded
            await page.goto(url, wait_until='load', timeout=30000)
            
            final_url = page.url
            print(f"Final URL: {final_url}")

            # Get the page content
            content = await page.content()

            # Save the HTML to a file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"Successfully downloaded and saved final HTML to {file_path}")

        except Exception as e:
            print(f"An error occurred with Playwright: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(get_final_page_source())
