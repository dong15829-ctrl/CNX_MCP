"""
Ultra Stealth Crawler Utilities
최신 안티-디텍션 기술을 활용한 고급 스텔스 크롤러
"""

import asyncio
import random
import json
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

class UltraStealth:
    """최신 스텔스 기술을 활용한 크롤러 유틸리티"""
    
    # 실제 사용자 에이전트 풀 (최신 버전)
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Chrome on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    
    # 실제 화면 해상도
    SCREEN_RESOLUTIONS = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1440, "height": 900},
        {"width": 2560, "height": 1440},
    ]
    
    # 실제 언어 설정
    LANGUAGES = [
        "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "ko-KR,ko;q=0.9",
        "en-US,en;q=0.9,ko;q=0.8",
    ]
    
    # 실제 타임존
    TIMEZONES = [
        "Asia/Seoul",
        "Asia/Tokyo",
        "America/New_York",
    ]
    
    @staticmethod
    async def create_ultra_stealth_context(
        playwright,
        headless: bool = True,
        proxy: Optional[Dict[str, str]] = None
    ) -> tuple[BrowserContext, Browser]:
        """
        최신 안티-디텍션 기술을 적용한 브라우저 컨텍스트 생성
        
        Args:
            playwright: Playwright 인스턴스
            headless: 헤드리스 모드 여부
            proxy: 프록시 설정 (선택)
            
        Returns:
            (context, browser) 튜플
        """
        
        # 랜덤 설정 선택
        user_agent = random.choice(UltraStealth.USER_AGENTS)
        resolution = random.choice(UltraStealth.SCREEN_RESOLUTIONS)
        language = random.choice(UltraStealth.LANGUAGES)
        timezone = random.choice(UltraStealth.TIMEZONES)
        
        # 브라우저 실행 인자 (최신 안티-디텍션)
        launch_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-features=BlockInsecurePrivateNetworkRequests',
            f'--window-size={resolution["width"]},{resolution["height"]}',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--disable-breakpad',
            '--disable-client-side-phishing-detection',
            '--disable-component-extensions-with-background-pages',
            '--disable-default-apps',
            '--disable-extensions',
            '--disable-features=TranslateUI',
            '--disable-hang-monitor',
            '--disable-ipc-flooding-protection',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-renderer-backgrounding',
            '--disable-sync',
            '--force-color-profile=srgb',
            '--metrics-recording-only',
            '--no-first-run',
            '--enable-automation=false',
            '--password-store=basic',
            '--use-mock-keychain',
            '--enable-features=NetworkService,NetworkServiceInProcess',
            '--disable-features=VizDisplayCompositor',
        ]
        
        # 브라우저 실행
        browser = await playwright.chromium.launch(
            headless=headless,
            args=launch_args,
            proxy=proxy
        )
        
        # 컨텍스트 생성 (고급 설정)
        context = await browser.new_context(
            viewport=resolution,
            user_agent=user_agent,
            locale=language.split(',')[0],
            timezone_id=timezone,
            permissions=['geolocation', 'notifications'],
            geolocation={"latitude": 37.5665, "longitude": 126.9780},  # Seoul
            color_scheme='light',
            device_scale_factor=1,
            has_touch=False,
            is_mobile=False,
            java_script_enabled=True,
            extra_http_headers={
                'Accept-Language': language,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
        )
        
        # 컨텍스트에 스텔스 스크립트 추가
        await context.add_init_script("""
            // WebDriver 속성 제거
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Chrome 객체 추가
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Permissions API 오버라이드
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Plugin 배열 추가
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Languages 설정
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en']
            });
            
            // Platform 설정
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            
            // Hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            // Device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            
            // Connection
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                })
            });
            
            // Battery API
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1
            });
            
            // Media devices
            navigator.mediaDevices.enumerateDevices = () => Promise.resolve([
                {deviceId: 'default', kind: 'audioinput', label: '', groupId: ''},
                {deviceId: 'default', kind: 'videoinput', label: '', groupId: ''},
                {deviceId: 'default', kind: 'audiooutput', label: '', groupId: ''}
            ]);
            
            // Canvas fingerprint 랜덤화
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                if (type === 'image/png' && this.width === 280 && this.height === 60) {
                    const context = this.getContext('2d');
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.floor(Math.random() * 10) - 5;
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, arguments);
            };
            
            // WebGL fingerprint 랜덤화
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
            
            // AudioContext fingerprint 랜덤화
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                const originalCreateOscillator = AudioContext.prototype.createOscillator;
                AudioContext.prototype.createOscillator = function() {
                    const oscillator = originalCreateOscillator.apply(this, arguments);
                    const originalStart = oscillator.start;
                    oscillator.start = function() {
                        arguments[0] = arguments[0] + (Math.random() * 0.0001);
                        return originalStart.apply(this, arguments);
                    };
                    return oscillator;
                };
            }
            
            // Screen 속성 설정
            Object.defineProperty(screen, 'availWidth', {
                get: () => window.innerWidth
            });
            Object.defineProperty(screen, 'availHeight', {
                get: () => window.innerHeight
            });
            
            // Date.prototype.getTimezoneOffset 오버라이드
            const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
            Date.prototype.getTimezoneOffset = function() {
                return -540; // Seoul timezone (UTC+9)
            };
            
            console.log('🔒 Ultra Stealth Mode Activated');
        """)
        return context, browser
    
    @staticmethod
    async def human_like_delay(min_ms: int = 1000, max_ms: int = 3000):
        """인간처럼 랜덤한 지연"""
        delay = random.uniform(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    @staticmethod
    async def random_mouse_movement(page: Page):
        """랜덤한 마우스 움직임 시뮬레이션"""
        try:
            viewport = page.viewport_size
            if viewport:
                for _ in range(random.randint(2, 5)):
                    x = random.randint(0, viewport['width'])
                    y = random.randint(0, viewport['height'])
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
        except:
            pass
    
    @staticmethod
    async def human_typing(page: Page, selector: str, text: str):
        """인간처럼 타이핑"""
        try:
            await page.wait_for_selector(selector, timeout=10000)
            await page.locator(selector).scroll_into_view_if_needed()
            await UltraStealth.human_like_delay(300, 700)
            
            await page.focus(selector)
            await UltraStealth.human_like_delay(200, 500)
            
            await page.fill(selector, "")
            await UltraStealth.human_like_delay(100, 300)
            
            for char in text:
                await page.type(selector, char, delay=random.uniform(50, 150))
                if random.random() < 0.1:  # 10% 확률로 짧은 멈춤
                    await asyncio.sleep(random.uniform(0.3, 0.8))
            
            await UltraStealth.human_like_delay(500, 1000)
            
        except Exception as e:
            print(f"   ⚠️  human_typing error: {e}")
            await page.fill(selector, text)
            await asyncio.sleep(0.5)
    
    @staticmethod
    async def random_scroll(page: Page, scrolls: int = 3):
        """랜덤한 스크롤 동작"""
        for _ in range(scrolls):
            scroll_amount = random.randint(300, 800)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await UltraStealth.human_like_delay(800, 1500)
            
            # 가끔 위로 스크롤
            if random.random() < 0.2:
                await page.evaluate(f"window.scrollBy(0, -{random.randint(100, 300)})")
                await UltraStealth.human_like_delay(500, 1000)
    
    @staticmethod
    async def simulate_reading(page: Page, duration_ms: int = 3000):
        """페이지 읽기 시뮬레이션"""
        await UltraStealth.human_like_delay(duration_ms, duration_ms + 2000)
        await UltraStealth.random_mouse_movement(page)


# 편의 함수
async def get_ultra_stealth_context(playwright, headless: bool = True, proxy: Optional[Dict] = None):
    """Ultra Stealth 컨텍스트 생성 (편의 함수)"""
    return await UltraStealth.create_ultra_stealth_context(playwright, headless, proxy)
