import asyncio
import random
from playwright.async_api import async_playwright, BrowserContext
from fake_useragent import UserAgent

# Generate realistic user agents
ua = UserAgent()

async def get_advanced_stealth_context(playwright, headless=True) -> BrowserContext:
    """
    Creates an advanced stealth browser context with comprehensive anti-detection measures.
    """
    # Launch browser with extensive flags to avoid detection
    browser = await playwright.chromium.launch(
        headless=headless,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-features=BlockInsecurePrivateNetworkRequests',
        ]
    )
    
    # Create context with realistic settings
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent=ua.random,
        locale='ko-KR',
        timezone_id='Asia/Seoul',
        geolocation={'latitude': 37.5665, 'longitude': 126.9780},  # Seoul
        permissions=['geolocation'],
        color_scheme='light',
        device_scale_factor=1,
        has_touch=False,
        is_mobile=False,
        java_script_enabled=True,
        extra_http_headers={
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
    )
    
    # Comprehensive anti-detection scripts
    await context.add_init_script("""
        // Overwrite the `navigator.webdriver` property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });

        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin},
                    description: "",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                },
                {
                    0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable", enabledPlugin: Plugin},
                    1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable", enabledPlugin: Plugin},
                    description: "",
                    filename: "internal-nacl-plugin",
                    length: 2,
                    name: "Native Client"
                }
            ],
        });

        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ko-KR', 'ko', 'en-US', 'en'],
        });

        // Add chrome object
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };

        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // Overwrite the `plugins` property to use a custom getter
        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => [
                {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                {type: "application/x-nacl", suffixes: "", description: "Native Client Executable", enabledPlugin: Plugin},
                {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable", enabledPlugin: Plugin}
            ],
        });

        // Mock battery API
        Object.defineProperty(navigator, 'getBattery', {
            value: () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1,
                addEventListener: () => {},
                removeEventListener: () => {},
                dispatchEvent: () => true
            })
        });

        // Mock connection
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 50,
                downlink: 10,
                saveData: false
            })
        });

        // Mock hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });

        // Mock device memory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });

        // Override toString methods
        const originalToString = Function.prototype.toString;
        Function.prototype.toString = function() {
            if (this === navigator.permissions.query) {
                return 'function query() { [native code] }';
            }
            return originalToString.call(this);
        };

        // Mock screen properties
        Object.defineProperty(screen, 'availWidth', {
            get: () => 1920
        });
        Object.defineProperty(screen, 'availHeight', {
            get: () => 1040
        });
        Object.defineProperty(screen, 'width', {
            get: () => 1920
        });
        Object.defineProperty(screen, 'height', {
            get: () => 1080
        });

        // Add realistic canvas fingerprint
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.call(this, parameter);
        };

        // Mock notification permission
        Object.defineProperty(Notification, 'permission', {
            get: () => 'default'
        });
    """)
    
    return context, browser


async def human_like_delay(min_ms=500, max_ms=2000):
    """Add human-like random delays"""
    await asyncio.sleep(random.uniform(min_ms/1000, max_ms/1000))


async def random_mouse_movement(page):
    """Simulate random mouse movements"""
    for _ in range(random.randint(2, 5)):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.1, 0.3))


async def human_typing(page, selector, text):
    """Type like a human with random delays"""
    try:
        # Wait for element to be available
        await page.wait_for_selector(selector, timeout=10000)
        
        # Scroll into view
        await page.locator(selector).scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.3, 0.7))
        
        # Focus on the element
        await page.focus(selector)
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        # Clear existing text
        await page.fill(selector, "")
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Type character by character
        for char in text:
            await page.type(selector, char, delay=random.uniform(50, 150))
        
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
    except Exception as e:
        print(f"   ⚠️  human_typing error: {e}")
        # Fallback: just fill the text
        await page.fill(selector, text)
        await asyncio.sleep(0.5)

