from typing import Optional, Dict, Any, List
import asyncio
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from src.quantum_qe_core.skills.browser import BrowserManager
from src.quantum_qe_core.skills.scanner import SecurityAuditor
from src.quantum_qe_core.skills.reporter import TestReporter
from src.quantum_qe_core.skills.knowledge import KnowledgeManager
from src.quantum_qe_core.skills.synthetic_data import SyntheticDataAgent
from src.quantum_qe_core.skills.telemetry_skill import LLMTelemetryHandler

class AuditorAgent:
    """
    AuditorAgent is responsible for the AppSec (Application Security) phase of the mission.
    It utilizes a ReAct loop to inspect the DOM state left by the Navigator, executing both 
    Passive and Active security scans against the OWASP Top 10 vulnerabilities.
    """
    def __init__(
        self, 
        browser_manager: BrowserManager, 
        reporter: Optional[TestReporter] = None, 
        knowledge_manager: Optional[KnowledgeManager] = None,
        llm_telemetry: Optional[LLMTelemetryHandler] = None
    ) -> None:
        self.scanner = SecurityAuditor()
        self.browser = browser_manager
        self.reporter = reporter
        self.knowledge = knowledge_manager
        self.llm_telemetry = llm_telemetry
        self.synthetic_data = SyntheticDataAgent()
        
        callbacks = [self.llm_telemetry] if self.llm_telemetry else []
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, max_retries=1, callbacks=callbacks)
        
        # Tools depend on browser manager instance
        self.tools: List[Any] = self.scanner.get_tools(self.browser) + self.synthetic_data.get_tools()
        if self.knowledge:
            self.tools.extend(self.knowledge.get_tools())
            
        self.agent_graph = self._setup_agent()

    def _setup_agent(self) -> Any:
        """
        Configures the LangGraph ReAct agent with specific security constraints and tools.
        """
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

    async def run(self, instruction: str) -> Dict[str, Any]:
        """
        Executes the Auditor Agent's intelligence loop.
        
        Args:
            instruction (str): The specific security auditing directive provided by the Orchestrator.
            
        Returns:
            Dict[str, Any]: A dictionary containing the textual summary and the list of JSON structured findings.
        """
        print(f"[AUDITOR] Running with instruction: {instruction}")
        inputs = {"messages": [{"role": "user", "content": instruction}]}
        # Enforce Recursion Limit and Hardware Timeout
        result = await asyncio.wait_for(
            self.agent_graph.ainvoke(inputs, config={"recursion_limit": 10}),
            timeout=300
        )
        
        messages = result.get("messages", [])
        if messages and hasattr(messages[-1], "content"):
            summary = messages[-1].content
        else:
            summary = "No response from Auditor."
            
        return {
            "summary": summary,
            "findings": self.scanner.get_findings()
        }
