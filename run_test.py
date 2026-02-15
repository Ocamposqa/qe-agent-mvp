import subprocess
import sys
import os

# Ensure env vars are set
os.environ["LANGCHAIN_TRACING_V2"] = "false"

print("Starting test execution...")
try:
    # Run main.py using the current python executable
    result = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True, encoding='utf-8')
    
    with open("run_output.txt", "w", encoding="utf-8") as f:
        f.write("=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr)
        
    print("Output written to run_output.txt")
        
except Exception as e:
    print(f"Error running test: {e}")
