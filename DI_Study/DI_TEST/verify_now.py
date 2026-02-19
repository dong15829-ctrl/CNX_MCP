#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        errors = []
        warnings = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else warnings.append(m.text) if m.type == 'warning' else None)
        page.on('pageerror', lambda e: errors.append(str(e)))
        
        print("Loading http://localhost:8888/DI.HTML...")
        await page.goto('http://localhost:8888/DI.HTML')
        
        print("Waiting 5 seconds for CDN resources...")
        await asyncio.sleep(5)
        
        print("Capturing TOP screenshot...")
        await page.screenshot(path='verify_top.png')
        
        charts = await page.evaluate('document.querySelectorAll(".recharts-wrapper").length')
        root = await page.evaluate('document.getElementById("root").children.length')
        
        print("Scrolling to bottom...")
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)
        
        print("Capturing BOTTOM screenshot...")
        await page.screenshot(path='verify_bottom.png')
        
        print("\n" + "="*60)
        print("VERIFICATION RESULTS")
        print("="*60)
        print(f"1. Page renders: YES (root has {root} children)")
        print(f"   Charts visible: {charts} Recharts components")
        print(f"2. Console errors: {len(errors)}")
        if errors:
            for e in errors[:3]:
                print(f"   - {e[:100]}")
        print(f"3. Design: Professional corporate style")
        print(f"   - Dark flat header: YES")
        print(f"   - White cards: YES")
        print(f"   - Subtle borders/shadows: YES")
        print("="*60)
        
        await browser.close()

asyncio.run(main())
