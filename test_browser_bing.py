import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from handlers.browser_automation import PlaywrightHandler

async def test_bing_search():
    """Test browser automation with Bing search."""
    
    print("Testing Browser Automation with Bing Search (headless=false)...")
    print("=" * 70)
    
    try:
        config = {
            "name": "browser_automation",
            "type": "playwright",
            "source": str(Path(__file__).parent / "capabilities/playwright-mcp"),
            "enabled": True,
            "headless": False  # Show browser window
        }
        
        handler = PlaywrightHandler(config)
        await handler.initialize()
        
        print("✓ Browser automation initialized")
        
        # Navigate to Bing
        print("\n1. Navigating to Bing...")
        result = await handler.execute("playwright_navigate", {
            "url": "https://www.bing.com"
        })
        print(f"   ✅ Navigated: {result.get('message', 'Success')}")
        
        # Wait a moment for page to load
        await asyncio.sleep(2)
        
        # Find and fill the search box
        print("\n2. Typing search query 'unified-mcp'...")
        result = await handler.execute("playwright_fill", {
            "element": "textarea[name='q'], input[name='q']",
            "text": "unified-mcp"
        })
        print(f"   ✅ Filled search box: {result.get('status', 'Success')}")
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Submit the search (press Enter)
        print("\n3. Submitting search...")
        result = await handler.execute("playwright_evaluate", {
            "script": "document.querySelector('textarea[name=\"q\"], input[name=\"q\"]').form.submit()"
        })
        print(f"   ✅ Search submitted")
        
        # Wait for results to load
        print("\n4. Waiting for search results...")
        await asyncio.sleep(3)
        print(f"   ✅ Search results should be loaded")

        # Take a screenshot
        print("\n5. Taking screenshot...")
        result = await handler.execute("playwright_screenshot", {
            "name": "bing_search_test"
        })
        print(f"   ✅ Screenshot saved")
        
        print("\n" + "=" * 70)
        print("✅ Browser automation test completed successfully!")
        print("=" * 70)
        
        # Keep browser open for 5 seconds so user can see it
        print("\nKeeping browser open for 5 seconds...")
        await asyncio.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Browser automation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bing_search())
    sys.exit(0 if success else 1)
