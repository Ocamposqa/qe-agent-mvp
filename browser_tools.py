import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def start(self):
        """Initializes the browser instance."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.page = await self.browser.new_page()

    async def navigate(self, url: str) -> dict:
        """Navigates to a specific URL and returns the simplified DOM."""
        if not self.page:
            await self.start()
        await self.page.goto(url)
        # Wait for network idle to ensure page is loaded
        await self.page.wait_for_load_state("networkidle")
        return await self.get_simplified_dom()

    async def click_element(self, selector: str) -> str:
        """Clicks an element based on a CSS selector."""
        if not self.page:
            return "Error: Browser not started."
        try:
            await self.page.click(selector, timeout=2000)
            return f"Successfully clicked element with selector: {selector}"
        except Exception as e:
            return f"Failed to click element: {str(e)}"

    async def type_text(self, selector: str, text: str) -> str:
        """Types text into an element."""
        if not self.page:
            return "Error: Browser not started."
        try:
            await self.page.fill(selector, text)
            return f"Successfully typed '{text}' into {selector}"
        except Exception as e:
            return f"Failed to type text: {str(e)}"

    async def get_simplified_dom(self) -> dict:
        """Returns a simplified version of the DOM for the LLM and a screenshot."""
        if not self.page:
            return {"text": "", "image": None}
        
        # Capture screenshot
        screenshot_bytes = await self.page.screenshot(type="jpeg")
        import base64
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        
        content = await self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "svg"]):
            script.decompose()

        # Simplify structure - focusing on interactive elements
        interactive_elements = []
        for tag in soup.find_all(['a', 'button', 'input', 'select', 'textarea', 'form']):
             # Get relevant attributes
             attrs = []
             if tag.get('id'): attrs.append(f"id='{tag['id']}'")
             if tag.get('name'): attrs.append(f"name='{tag['name']}'")
             if tag.get('class'): attrs.append(f"class='{' '.join(tag['class'])}'")
             if tag.get('placeholder'): attrs.append(f"placeholder='{tag['placeholder']}'")
             if tag.get('href'): attrs.append(f"href='{tag['href']}'")
             if tag.get('type'): attrs.append(f"type='{tag['type']}'")
             
             text = tag.get_text(strip=True)
             attr_str = " ".join(attrs)
             
             interactive_elements.append(f"<{tag.name} {attr_str}>{text}</{tag.name}>")

        # Also get text content for context, but limit it
        body_text = soup.body.get_text(separator=' ', strip=True)[:1000] if soup.body else ""
        
        context_text = f"Page Context:\n{body_text}\n\nInteractive Elements:\n" + "\n".join(interactive_elements)
        
        return {
            "text": context_text,
            "image": screenshot_b64
        }

    async def take_screenshot(self, filename: str):
        """Saves a screenshot to a file."""
        if self.page:
            await self.page.screenshot(path=filename)

    async def stop(self):
        """Closes the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
