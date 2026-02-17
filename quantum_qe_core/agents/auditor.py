from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from quantum_qe_core.skills.browser import BrowserManager
from quantum_qe_core.skills.scanner import SecurityAuditor
from quantum_qe_core.skills.reporter import TestReporter
from quantum_qe_core.skills.knowledge import KnowledgeManager

class AuditorAgent:
    def __init__(self, browser_manager: BrowserManager, reporter: TestReporter = None, knowledge_manager: KnowledgeManager = None):
        self.scanner = SecurityAuditor()
        self.browser = browser_manager
        self.reporter = reporter
        self.knowledge = knowledge_manager
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # Tools depend on browser manager instance
        self.tools = self.scanner.get_tools(self.browser)
        if self.knowledge:
            self.tools.extend(self.knowledge.get_tools())
            
        self.agent_graph = self._setup_agent()

    def _setup_agent(self):
        system_message = """You are the 'Auditor Agent' (AppSec Specialist).
Your goal is to identify security vulnerabilities.

# Responsibilities:
1. Perform Passive Analysis (Headers, Cookies).
2. Perform Active Scanning (Fuzzing) on identified inputs.
3. Classify findings by severity (Critical, High, Medium, Low).
4. Report vulnerabilities with clear remediation steps.
5. Consult 'SearchSecurityStandards' (RAG) to validate findings against OWASP.

# Constraints:
- You operate on the page that the Navigator has already navigated to.
- Use 'SecurityActiveScan' and 'SecurityPassiveScan' tools.
- Use 'SearchSecurityStandards' for additional context on vulnerabilities.
- Do NOT navigate away unless indispensable.
"""
        model_with_tools = self.llm.bind_tools(self.tools, parallel_tool_calls=False)
        return create_react_agent(model_with_tools, self.tools, prompt=system_message)

    async def run(self, instruction: str):
        print(f"[AUDITOR] Running with instruction: {instruction}")
        inputs = {"messages": [{"role": "user", "content": instruction}]}
        result = await self.agent_graph.ainvoke(inputs)
        
        messages = result.get("messages", [])
        if messages and hasattr(messages[-1], "content"):
            return messages[-1].content
        return "No response from Auditor."
