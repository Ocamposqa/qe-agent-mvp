import sys
import os
sys.path.append(os.getcwd())

try:
    print("Importing BrowserManager...")
    from quantum_qe_core.skills.browser import BrowserManager
    print("BrowserManager Imported.")
    print("Importing NavigatorAgent...")
    from quantum_qe_core.agents.navigator import NavigatorAgent
    print("NavigatorAgent Imported.")
except Exception as e:
    print(f"Import Failed: {e}")
    import traceback
    traceback.print_exc()
