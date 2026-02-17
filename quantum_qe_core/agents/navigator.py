from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from quantum_qe_core.skills.browser import BrowserManager
from quantum_qe_core.skills.reporter import TestReporter

class NavigatorAgent:
    def __init__(self, browser_manager: BrowserManager, reporter: TestReporter = None):
        self.browser = browser_manager
        self.reporter = reporter
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.tools = self.browser.get_tools(self.reporter)
        self.agent_graph = self._setup_agent()

    def _setup_agent(self):
        system_message = """You are the 'Navigator Agent' (UI Specialist).
Your goal is to perform functional testing on web applications.

# Responsibilities:
1. Navigate to target URLs.
2. Interact with the UI (Click, Type) to complete user flows.
3. Validate functionality (look for success messages, correct page states).
4. Report any functional bugs or visual issues.

# Constraints:
- Do NOT perform security scanning or active fuzzing. That is the job of the Auditor Agent.
- Analyze the DOM to understand the page structure.
- Execute tools sequentially.
"""
        model_with_tools = self.llm.bind_tools(self.tools, parallel_tool_calls=False)
        return create_react_agent(model_with_tools, self.tools, prompt=system_message)
    
    async def run(self, instruction: str):
        print(f"[NAVIGATOR] Running with instruction: {instruction}")
        inputs = {"messages": [{"role": "user", "content": instruction}]}
        result = await self.agent_graph.ainvoke(inputs)
        
        messages = result.get("messages", [])
        if messages and hasattr(messages[-1], "content"):
            return messages[-1].content
        return "No response from Navigator."
