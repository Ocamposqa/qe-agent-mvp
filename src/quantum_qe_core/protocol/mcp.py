from abc import ABC, abstractmethod

class MCPTool(ABC):
    """Model Context Protocol (MCP) Standard Interface."""
    
    @abstractmethod
    def name(self) -> str:
        """Helper to return tool name."""
        raise NotImplementedError
    
    @abstractmethod
    def description(self) -> str:
        """Helper to return tool description."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, **kwargs):
        """Execute the tool with given arguments."""
        pass

class JiraConnector(MCPTool):
    """Placeholder for future Jira integration via MCP."""
    
    def name(self):
        return "jira_create_issue"
        
    def description(self):
        return "Creates a new issue in JIRA."
        
    def execute(self, **kwargs):
        summary = kwargs.get('summary', 'No summary provided')
        # Implementation to come
        print(f"[MCP-Mock] Jira Issue Created: {summary}")
        return {"id": "JIRA-123", "status": "created"}
