import os
from langchain_core.tools import Tool

class KnowledgeManager:
    def __init__(self, knowledge_path: str):
        self.knowledge_path = knowledge_path

    def get_tools(self):
        
        def search_knowledge_wrapper(query: str):
            """Searches the knowledge base for a query."""
            results = []
            # Simple grep-like search for now
            for root, _, files in os.walk(self.knowledge_path):
                for file in files:
                    if file.endswith(".md"):
                        path = os.path.join(root, file)
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                content = f.read()
                                if query.lower() in content.lower():
                                    # meaningful snippet? just return first 500 chars surrounding match?
                                    idx = content.lower().find(query.lower())
                                    start = max(0, idx - 100)
                                    end = min(len(content), idx + 400)
                                    results.append(f"Match in {file}:\n...{content[start:end]}...\n")
                        except Exception as e:
                            continue
            
            if not results:
                return f"No knowledge found for query: {query}"
            return "\n".join(results)[:2000] # Limit output size

        return [
            Tool(
                name="SearchSecurityStandards",
                func=search_knowledge_wrapper,
                description="Searches OWASP and SQA standards. Input: usage query (e.g. 'SQL Injection')."
            )
        ]
