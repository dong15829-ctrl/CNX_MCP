import random
from playwright.async_api import async_playwright, BrowserContext

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
]

async def get_stealth_context(playwright, headless=True, user_agent: str | None = None) -> BrowserContext:
    """
    Creates a Playwright browser context with stealth settings.
    """
    browser = await playwright.chromium.launch(
        headless=headless,
        chromium_sandbox=False,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-seccomp-filter-sandbox',
            '--disable-namespace-sandbox',
            '--single-process',
        ],
    )
    
    user_agent = user_agent or random.choice(USER_AGENTS)
    
    context = await browser.new_context(
        user_agent=user_agent,
        viewport={"width": 1920, "height": 1080},
        locale="ko-KR",
        timezone_id="Asia/Seoul",
        permissions=["geolocation"],
        geolocation={"latitude": 37.5665, "longitude": 126.9780}, # Seoul
        java_script_enabled=True,
    )
    
    # Anti-detection scripts
    await context.add_init_script("""
        // Pass the Webdriver Test.
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Pass the Chrome Test.
        window.chrome = {
            runtime: {},
        };

        // Pass the Plugins Length Test.
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });

        // Pass the Languages Test.
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ko-KR', 'ko', 'en-US', 'en'],
        });
    """)
    
    return context, browser
