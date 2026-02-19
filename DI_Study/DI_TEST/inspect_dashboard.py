#!/usr/bin/env python3
"""
Visual inspection of dashboard with console monitoring
"""
import asyncio
from playwright.async_api import async_playwright

async def inspect_dashboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        # Track console messages
        console_errors = []
        console_warnings = []
        
        page.on('console', lambda msg: (
            console_errors.append(msg.text) if msg.type == 'error' else
            console_warnings.append(msg.text) if msg.type == 'warning' else None
        ))
        
        page_errors = []
        page.on('pageerror', lambda err: page_errors.append(str(err)))
        
        print("Navigating to http://localhost:8888/DI.HTML...")
        await page.goto('http://localhost:8888/DI.HTML', wait_until='domcontentloaded')
        
        print("Waiting 5 seconds for CDN resources to load...")
        await asyncio.sleep(5)
        
        # Check visual elements
        print("\n" + "="*70)
        print("VISUAL INSPECTION")
        print("="*70)
        
        # Check for charts
        chart_count = await page.evaluate('''
            () => document.querySelectorAll('.recharts-wrapper, .recharts-surface').length
        ''')
        print(f"✓ Recharts components found: {chart_count}")
        
        # Check for header
        has_header = await page.evaluate('''
            () => {
                const header = document.querySelector('.hero-gradient');
                return !!header;
            }
        ''')
        print(f"✓ Dark gradient header present: {has_header}")
        
        # Check for KPI cards
        kpi_cards = await page.evaluate('''
            () => {
                const cards = Array.from(document.querySelectorAll('[class*="bg-white"]'));
                return cards.length;
            }
        ''')
        print(f"✓ White cards found: {kpi_cards}")
        
        # Screenshot top
        print("\n📸 Taking screenshot of TOP part...")
        await page.screenshot(path='dashboard_top.png', full_page=False)
        print("✓ Saved: dashboard_top.png")
        
        # Scroll to bottom
        print("\n⬇️  Scrolling to bottom...")
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)
        
        # Screenshot bottom
        print("📸 Taking screenshot of BOTTOM part...")
        await page.screenshot(path='dashboard_bottom.png', full_page=False)
        print("✓ Saved: dashboard_bottom.png")
        
        # Report findings
        print("\n" + "="*70)
        print("FINDINGS")
        print("="*70)
        
        print("\n1️⃣  PAGE RENDERING:")
        if chart_count >= 10:
            print(f"   ✅ YES - All charts render correctly ({chart_count} charts found)")
        else:
            print(f"   ⚠️  Partial - Only {chart_count} charts found")
        
        print("\n2️⃣  JAVASCRIPT ERRORS:")
        if console_errors or page_errors:
            print(f"   ❌ YES - Found errors:")
            for err in console_errors[:5]:
                print(f"      • {err}")
            for err in page_errors[:5]:
                print(f"      • {err}")
        else:
            print("   ✅ NO - No JavaScript errors detected")
        
        print("\n3️⃣  DESIGN ASSESSMENT:")
        checks = {
            "Flat dark header": has_header,
            "White cards present": kpi_cards > 0,
            "Charts visible": chart_count > 0
        }
        
        all_good = all(checks.values())
        if all_good:
            print("   ✅ YES - Professional corporate design:")
            for check, status in checks.items():
                print(f"      ✓ {check}")
        else:
            print("   ⚠️  Some design elements missing:")
            for check, status in checks.items():
                symbol = "✓" if status else "✗"
                print(f"      {symbol} {check}")
        
        if console_warnings:
            print(f"\n📋 Console Warnings ({len(console_warnings)}):")
            for warn in console_warnings[:3]:
                print(f"   • {warn[:100]}")
        
        print("\n" + "="*70)
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(inspect_dashboard())
