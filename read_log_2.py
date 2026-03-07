import sys
filename = r"c:\Users\CarlosAlbertoOcampoO\.gemini\antigravity\scratch\qe-agent-mvp\orchestrator.log"
with open(filename, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()
    for i in range(1025, min(1120, len(lines))):
        print(f"[{i+1}] {lines[i].strip()}")
