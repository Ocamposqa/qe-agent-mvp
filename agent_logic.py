from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from browser_tools import BrowserManager
import asyncio

from reporting import TestReporter

class QEAgent:
    def __init__(self, browser_manager: BrowserManager, reporter: TestReporter = None):
        self.browser = browser_manager
        self.reporter = reporter
        # Use model name string or instance. create_agent accepts both.
        # But create_agent with specific model instance is better if we want config.
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.tools = self._setup_tools()
        self.agent_graph = self._setup_agent()

    def _setup_tools(self):
        def ask_human(question: str) -> str:
            """Asks the human user for help or clarification."""
            print(f"\n[AGENT QUERY]: {question}")
            answer = input("[USER RESPONSE]: ")
            if self.reporter:
                self.reporter.add_step(f"Asked Human: {question}", "INFO")
                self.reporter.add_step(f"Human Answered: {answer}", "INFO")
            return answer

        async def navigate_wrapper(url: str):
            print(f"[DEBUG] navigate_wrapper called with {url}")
            result = await self.browser.navigate(url)
            
            # Log step
            if self.reporter:
                # We can take a dedicated screenshot for the report
                filename = f"report_screenshots/step_{len(self.reporter.steps)}.jpg"
                import os
                os.makedirs("report_screenshots", exist_ok=True)
                await self.browser.take_screenshot(filename)
                self.reporter.add_step(f"Navigated to {url}", "PASS", filename)
                print(f"[DEBUG] Screenshot saved to {filename}")

            if isinstance(result, dict):
                return result.get("text", "No content") 
            return result

        async def click_wrapper(selector: str):
            result = await self.browser.click_element(selector)
            if self.reporter:
                # Capture result
                status = "PASS" if "Successfully" in result else "FAIL"
                filename = f"report_screenshots/step_{len(self.reporter.steps)}.jpg"
                import os
                os.makedirs("report_screenshots", exist_ok=True)
                await self.browser.take_screenshot(filename)
                self.reporter.add_step(f"Clicked {selector}. Result: {result}", status, filename)
            return result

        async def type_wrapper(input_str: str):
            selector, text = input_str.split("|", 1)
            result = await self.browser.type_text(selector, text)
            if self.reporter:
                 status = "PASS" if "Successfully" in result else "FAIL"
                 filename = f"report_screenshots/step_{len(self.reporter.steps)}.jpg"
                 import os
                 os.makedirs("report_screenshots", exist_ok=True)
                 await self.browser.take_screenshot(filename)
                 self.reporter.add_step(f"Typed '{text}' into {selector}", status, filename)
            return result

        async def get_context_wrapper(x):
            result = await self.browser.get_simplified_dom()
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
            ),
            Tool(
                name="AskHuman",
                func=ask_human,
                description="Asks the user for help. Use this if you are stuck, unsure, or need validation. Input: The question to ask."
            )
        ]

    def _setup_agent(self):
        system_message = """You are an Autonomous Quality Engineering (QE) Agent.
Your goal is to test web applications.
- Analyze the page context (DOM) to understand the state.
- If the DOM is confusing or you are stuck, use the 'AskHuman' tool.
- When validating, look for success messages or specific element states.
- If you find a bug, report it.
"""
        # Using langgraph prebuilt agent
        return create_react_agent(
            self.llm,
            self.tools,
            prompt=system_message,
        )

    async def run(self, instruction: str):
        """Runs the agent with a specific instruction."""
        print(f"[DEBUG] Agent running with instruction: {instruction}")
        inputs = {"messages": [{"role": "user", "content": instruction}]}
        
        # Invoke the graph asynchronously
        print(f"[DEBUG] Invoking agent graph... Type: {type(self.agent_graph)}")
        result = await self.agent_graph.ainvoke(inputs)
        print(f"[DEBUG] Agent invocation complete. Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        # Extract the last message content
        messages = result.get("messages", [])
        if messages and hasattr(messages[-1], "content"):
            return messages[-1].content
        return "No response from agent."
