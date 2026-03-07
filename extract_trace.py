import sys
filename = r"c:\Users\CarlosAlbertoOcampoO\.gemini\antigravity\scratch\qe-agent-mvp\orchestrator.log"
out_filename = r"c:\Users\CarlosAlbertoOcampoO\.gemini\antigravity\scratch\qe-agent-mvp\extracted_trace.txt"

with open(filename, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

with open(out_filename, "w", encoding="utf-8") as out:
    for i in range(1025, min(1130, len(lines))):
        out.write(f"[{i+1}] {lines[i].strip()}\n")
