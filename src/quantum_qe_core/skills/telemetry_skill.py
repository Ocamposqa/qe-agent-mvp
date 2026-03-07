from langchain_core.callbacks import BaseCallbackHandler
from typing import Dict, Any

class LLMTelemetryHandler(BaseCallbackHandler):
    """
    Intercepts LLM calls to register token usage and calculate estimated costs.
    """
    def __init__(self):
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.successful_requests = 0
        
    def on_llm_end(self, response, **kwargs: Any) -> Any:
        # response is an LLMResult
        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            self.total_tokens += usage.get("total_tokens", 0)
            self.prompt_tokens += usage.get("prompt_tokens", 0)
            self.completion_tokens += usage.get("completion_tokens", 0)
            self.successful_requests += 1

    def get_estimated_cost(self):
        # Rough estimation based on GPT-4o costs ($5/1M input, $15/1M output)
        return (self.prompt_tokens / 1000000) * 5.0 + (self.completion_tokens / 1000000) * 15.0

class NetworkTelemetry:
    """
    Captures Playwright network metrics (bytes transferred).
    """
    def __init__(self):
        self.total_bytes_received = 0
        self.total_requests = 0

    async def handle_response(self, response):
        self.total_requests += 1
        try:
            # getting body size might fail if the response is closed or a redirect
            headers = response.headers
            if 'content-length' in headers:
                self.total_bytes_received += int(headers['content-length'])
            else:
                body = await response.body()
                self.total_bytes_received += len(body)
        except Exception:
            pass

    def get_stats(self):
        return {
            "total_bytes_mb": round(self.total_bytes_received / (1024 * 1024), 2),
            "total_requests": self.total_requests
        }
