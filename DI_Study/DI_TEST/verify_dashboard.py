#!/usr/bin/env python3
"""
Comprehensive dashboard verification with design assessment
"""
import asyncio
from playwright.async_api import async_playwright

async def verify_dashboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        console_errors = []
        console_warnings = []
        page_errors = []
        
        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else console_warnings.append(msg.text) if msg.type == 'warning' else None)
        page.on('pageerror', lambda err: page_errors.append(str(err)))
        
        print("=" * 80)
        print("DASHBOARD VERIFICATION REPORT")
        print("=" * 80)
        
        print("\nNavigating to http://localhost:8888/DI.HTML...")
        response = await page.goto('http://localhost:8888/DI.HTML', wait_until='domcontentloaded')
        print(f"Response status: {response.status}")
        
        print("\nWaiting 5 seconds for CDN resources...")
        await asyncio.sleep(5)
        
        print("\nTaking screenshot of TOP...")
        await page.screenshot(path='verify_top.png', full_page=False)
        print("Saved: verify_top.png")
        
        react_data = await page.evaluate('''() => {
            const root = document.getElementById('root');
            const charts = document.querySelectorAll('.recharts-wrapper, .recharts-surface');
            return {
                hasContent: root && root.children.length > 0,
                chartCount: charts.length
            };
        }''')
        
        print(f"\nCharts found: {react_data['chartCount']}")
        
        print("\nScrolling to bottom...")
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)
        
        print("Taking screenshot of BOTTOM...")
        await page.screenshot(path='verify_bottom.png', full_page=False)
        print("Saved: verify_bottom.png")
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"1. Renders correctly: {'YES' if react_data['hasContent'] else 'NO'}")
        print(f"   Charts visible: {react_data['chartCount']}")
        print(f"2. Console errors: {len(console_errors)}")
        print(f"   Page errors: {len(page_errors)}")
        
        if console_errors:
            print("\n   Errors:")
            for err in console_errors[:5]:
                print(f"   - {err}")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(verify_dashboard())
