from typing import Optional, Any
import asyncio
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from src.quantum_qe_core.skills.browser import BrowserManager
from src.quantum_qe_core.skills.reporter import TestReporter

from langchain_core.tools import tool

@tool
def ask_human(question: str) -> str:
    """Ask the human user for help or clarification when you are stuck or need input."""
    print(f"\n[AGENT ASKS HUMAN]: {question}")
    # Use real input() to block and wait for user response
    try:
        answer = input("> ")
        return f"User Answer: {answer}"
    except (EOFError, KeyboardInterrupt):
        return "User refused to answer (EOF/Interrupt)."


class NavigatorAgent:
    """
    NavigatorAgent is responsible for standard Functional QA Testing. It navigates 
    target URLs, interacts with the DOM (clicking, typing), and validates UI state 
    changes without performing hostile active scanning.
    """
    def __init__(self, browser_manager: BrowserManager, reporter: Optional[TestReporter] = None) -> None:
        self.browser = browser_manager
        self.reporter = reporter
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, max_retries=1)
        self.tools = self.browser.get_tools(self.reporter) + [ask_human]
        self.agent_graph = self._setup_agent()

    def _setup_agent(self) -> Any:
        """
        Configures the LangGraph ReAct agent with specific navigation constraints and tools.
        """
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
- If you are stuck or encounter a timeout/error, use the 'ask_human' tool to request assistance.
"""
        model_with_tools = self.llm.bind_tools(self.tools, parallel_tool_calls=False)
        return create_react_agent(model_with_tools, self.tools, prompt=system_message)
    
    async def run(self, instruction: str) -> str:
        """
        Executes the Navigator Agent's intelligence loop.
        
        Args:
            instruction (str): The specific functional testing directive provided by the Orchestrator.
            
        Returns:
            str: A textual summary of the agent's actions and whether the test passed or failed.
        """
        print(f"[NAVIGATOR] Running with instruction: {instruction}")
        inputs = {"messages": [{"role": "user", "content": instruction}]}
        # Apply Recursion Limit (max 10 steps) and a Hardware Timeout (300 seconds)
        result = await asyncio.wait_for(
            self.agent_graph.ainvoke(inputs, config={"recursion_limit": 10}),
            timeout=300
        )
        
        messages = result.get("messages", [])
        if messages and hasattr(messages[-1], "content"):
            return str(messages[-1].content)
        return "No response from Navigator."
