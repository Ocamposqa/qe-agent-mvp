import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from langchain_core.tools import Tool
import uuid
import os

class BrowserManager:
    def __init__(self, headless: bool = False):
        self.playwright = None
        self.browser = None
        self.page = None
        self.headless = headless
        self.logs = []
        self.responses = []

    async def start(self):
        """Initializes the browser instance."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.page = await self.browser.new_page()
            
            # Capture console logs
            self.page.on("console", lambda msg: self.logs.append(f"[CONSOLE] {msg.type}: {msg.text}"))
            
            # Capture failed network requests
            self.page.on("requestfailed", lambda request: self.logs.append(f"[NETWORK] Failed: {request.url} - {request.failure}"))

            # Capture all network responses for security analysis
            async def handle_response(response):
                try:
                    headers = await response.all_headers()
                    self.responses.append({
                        "url": response.url,
                        "status": response.status,
                        "headers": headers
                    })
                except Exception as e:
                    pass # Ignore errors during capture to avoid noise

            self.page.on("response", handle_response)

    async def navigate(self, url: str) -> dict:
        """Navigates to a specific URL and returns the simplified DOM."""
        if not self.page:
            await self.start()
        try:
            await self.page.goto(url, timeout=30000) # 30s timeout
            # Wait for network idle to ensure page is loaded
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except Exception as e:
            error_msg = f"Navigation failed: {str(e)}"
            self.logs.append(f"[ERROR] {error_msg}")
            return {"text": f"Error: {error_msg}", "image": None}
            
        return await self.get_simplified_dom()

    async def click_element(self, selector: str) -> str:
        """Clicks an element based on a CSS selector."""
        if not self.page:
            return "Error: Browser not started."
        try:
            await self.page.click(selector, timeout=5000) # 5s timeout for interactions
            return f"Successfully clicked element with selector: {selector}"
        except Exception as e:
            return f"Failed to click element: {str(e)}"

    async def type_text(self, selector: str, text: str) -> str:
        """Types text into an element based on a CSS selector."""
        if not self.page:
            return "Error: Browser not started."
        try:
            await self.page.fill(selector, text, timeout=5000)
            return f"Successfully typed '{text}' into {selector}"
        except Exception as e:
            return f"Failed to type text: {str(e)}"

    async def press_key(self, selector: str, key: str) -> str:
        """Presses a specific key on an element."""
        if not self.page:
            return "Error: Browser not started."
        try:
            await self.page.press(selector, key, timeout=5000)
            return f"Successfully pressed '{key}' on {selector}"
        except Exception as e:
            return f"Failed to press key: {str(e)}"

    async def get_simplified_dom(self) -> dict:
        """Returns a simplified version of the DOM for the LLM and a screenshot."""
        if not self.page:
            return {"text": "", "image": None}
        
        try:
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
            for tag in soup.find_all(['a', 'button', 'input', 'select', 'textarea', 'form', 'div', 'span']):
                 # Basic attributes
                 attrs = []
                 if tag.get('id'): attrs.append(f"id='{tag['id']}'")
                 if tag.get('name'): attrs.append(f"name='{tag['name']}'")
                 if tag.get('class'): attrs.append(f"class='{' '.join(tag['class'])}'")
                 if tag.get('placeholder'): attrs.append(f"placeholder='{tag['placeholder']}'")
                 if tag.get('href'): attrs.append(f"href='{tag['href']}'")
                 if tag.get('type'): attrs.append(f"type='{tag['type']}'")
                 
                 # Robust attributes (Testing & Accessibility)
                 for attr in ['data-testid', 'data-test-id', 'data-cy', 'aria-label', 'role', 'title']:
                     if tag.get(attr):
                         attrs.append(f"{attr}='{tag[attr]}'")

                 # Only include divs/spans if they have relevant attributes or are interactive
                 if tag.name in ['div', 'span']:
                     if not any(k in tag.attrs for k in ['id', 'data-testid', 'data-test-id', 'data-cy', 'role', 'onclick']):
                         continue

                 text = tag.get_text(strip=True)
                 if not text and not attrs:
                     continue # Skip empty elements without attributes
                     
                 attr_str = " ".join(attrs)
                 
                 interactive_elements.append(f"<{tag.name} {attr_str}>{text}</{tag.name}>")

            # Also get text content for context, but limit it
            body_text = soup.body.get_text(separator=' ', strip=True)[:1000] if soup.body else ""
            
            context_text = f"Page Context:\n{body_text}\n\nInteractive Elements:\n" + "\n".join(interactive_elements)
            
            return {
                "text": context_text,
                "image": screenshot_b64
            }
        except Exception as e:
            error_msg = f"Failed to get DOM/Screenshot: {str(e)}"
            self.logs.append(f"[ERROR] {error_msg}")
            return {"text": f"Error: {error_msg}", "image": None}

    async def take_screenshot(self, filename: str):
        """Saves a screenshot to a file."""
        if self.page:
            await self.page.screenshot(path=filename)

    async def get_content(self) -> str:
        """Returns the raw HTML content of the page."""
        if self.page:
            return await self.page.content()
        return ""

    async def close(self):
        """Closes the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def get_logs(self):
        """Returns captured browser logs."""
        return self.logs
        
    async def get_responses(self):
        """Returns captured network responses."""
        return getattr(self, 'responses', [])

    async def get_cookies(self):
        """Returns all cookies from the current context."""
        if self.page:
            return await self.page.context.cookies()
        return []

    async def get_input_elements(self) -> list:
        """Returns a list of input elements for active scanning."""
        if not self.page:
            return []
        
        inputs = []
        try:
            # Find all input and textarea elements
            elements = await self.page.query_selector_all("input, textarea")
            for element in elements:
                # Skip hidden or submit/button inputs
                type_attr = await element.get_attribute("type")
                if type_attr in ["hidden", "submit", "button", "image", "reset"]:
                    continue
                
                # specific checks for visibility could be added here
                if not await element.is_visible():
                    continue

                # Construct a selector
                # Priority: id > name > others
                elem_id = await element.get_attribute("id")
                elem_name = await element.get_attribute("name")
                
                selector = ""
                if elem_id:
                    selector = f"#{elem_id}"
                elif elem_name:
                    selector = f"[name='{elem_name}']"
                else:
                    # Fallback to a less robust selector or skip
                    # leveraging playwright's locator logic would be better but simple CSS for now
                    continue 

                inputs.append({
                    "selector": selector,
                    "type": type_attr or "text",
                    "name": elem_name,
                    "id": elem_id
                })
        except Exception as e:
            self.logs.append(f"[ERROR] Failed to get input elements: {str(e)}")
            
        return inputs

    def get_tools(self, reporter=None):
        """Returns a list of LangChain Tools exposed by this skill."""
        
        async def navigate_wrapper(url: str):
            print(f"[DEBUG] navigate_wrapper called with {url}")
            result = await self.navigate(url)
            
            # Log step
            if reporter:
                step_uuid = str(uuid.uuid4())[:8]
                filename = f"report_screenshots/step_{len(reporter.steps)}_{step_uuid}.jpg"
                os.makedirs("report_screenshots", exist_ok=True)
                await self.take_screenshot(filename)
                reporter.add_step(f"Navigated to {url}", "PASS", filename)
                print(f"[DEBUG] Screenshot saved to {filename}")

            if isinstance(result, dict):
                return result.get("text", "No content") 
            return result

        async def click_wrapper(selector: str):
            print(f"[DEBUG] click_wrapper received: {selector}")
            result = await self.click_element(selector)
            if reporter:
                status = "PASS" if "Successfully" in result else "FAIL"
                step_uuid = str(uuid.uuid4())[:8]
                filename = f"report_screenshots/step_{len(reporter.steps)}_{step_uuid}.jpg"
                os.makedirs("report_screenshots", exist_ok=True)
                await self.take_screenshot(filename)
                reporter.add_step(f"Clicked {selector}. Result: {result}", status, filename)
            return result

        async def type_wrapper(input_str: str):
            print(f"[DEBUG] type_wrapper received: {input_str}")
            try:
                if "|" in input_str:
                    selector, text = input_str.split("|", 1)
                else:
                    return "Error: Input must be in format 'selector|text', e.g., '#username|myuser'"
                
                result = await self.type_text(selector, text)
            except Exception as e:
                return f"Error processing input '{input_str}': {e}"
            
            if reporter:
                 status = "PASS" if "Successfully" in result else "FAIL"
                 step_uuid = str(uuid.uuid4())[:8]
                 filename = f"report_screenshots/step_{len(reporter.steps)}_{step_uuid}.jpg"
                 os.makedirs("report_screenshots", exist_ok=True)
                 await self.take_screenshot(filename)
                 reporter.add_step(f"Typed '{text}' into {selector}", status, filename)
            return result

        async def get_context_wrapper(x):
            result = await self.get_simplified_dom()
            if isinstance(result, dict):
                 return result.get("text", "")
            return result

        return [
            Tool(
                name="Navigate",
                func=navigate_wrapper, 
                coroutine=navigate_wrapper,
                description="Navigates to a specific URL."
            ),
             Tool(
                name="ClickElement",
                func=click_wrapper,
                coroutine=click_wrapper,
                description="Clicks an element. Input: CSS selector."
            ),
            Tool(
                name="TypeText",
                func=type_wrapper,
                coroutine=type_wrapper,
                description="Types text. Input: 'selector|text'."
            ),
            Tool(
                name="GetPageContext",
                func=get_context_wrapper,
                coroutine=get_context_wrapper,
                description="Refreshes page view."
            )
        ]
