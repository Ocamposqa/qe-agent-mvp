import asyncio
from quantum_qe_core.api_server import _run_orchestrator_sync, ScanRequest

request = ScanRequest(
    url="https://google.com",
    instructions="test",
    skip_security=False,
    headless=True
)

print("Starting isolated test...")
try:
    _run_orchestrator_sync("test-id-1234", request)
    print("Test finished successfully!")
except Exception as e:
    import traceback
    print("Test failed with exception:")
    traceback.print_exc()
