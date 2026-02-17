from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os
from datetime import datetime

class TestReporter:
    def __init__(self, filename="test_report.pdf"):
        self.filename = filename
        self.steps = []
        self.start_time = datetime.now()

    def add_step(self, description: str, status: str = "INFO", screenshot_path: str = None):
        """Logs a step in the report."""
        self.steps.append({
            "timestamp": datetime.now(),
            "description": description,
            "status": status,
            "screenshot": screenshot_path
        })

    def add_browser_logs(self, logs: list):
        """Adds browser logs to the report."""
        if logs:
            self.steps.append({
                "timestamp": datetime.now(),
                "description": "Browser Logs Captured",
                "status": "INFO",
                "screenshot": None,
                "logs": logs
            })

    def add_security_findings(self, findings: list):
        """Adds security findings to the report."""
        if findings:
            self.steps.append({
                "timestamp": datetime.now(),
                "description": "Security Audit Completed",
                "status": "INFO",
                "screenshot": None,
                "security_findings": findings
            })

    def generate_report(self, filename=None):
        target_file = filename or self.filename
        # Ensure directory exists
        os.makedirs(os.path.dirname(target_file) or ".", exist_ok=True)
        c = canvas.Canvas(target_file, pagesize=letter)
        width, height = letter
        y = height - 50
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "QE Agent Test Report")
        y -= 30
        
        c.setFont("Helvetica", 10)
        
        for step in self.steps:
            if y < 100:
                c.showPage()
                y = height - 50
                
            timestamp = step["timestamp"].strftime("%H:%M:%S")
            # Truncate description if too long
            desc = (step["description"][:75] + '..') if len(step["description"]) > 75 else step["description"]
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, f"[{timestamp}] [{step['status']}] {desc}")
            y -= 15
            
            c.setFont("Helvetica", 9)
            if step["screenshot"] and os.path.exists(step["screenshot"]):
                try:
                    # Draw screenshot (scaled down)
                    img_width = 400
                    img_height = 225
                    
                    # Check if we have space, else new page
                    display_height = img_height
                    display_width = img_width
                    
                    if y - display_height < 50:
                        c.showPage()
                        y = height - 50
                    
                    c.drawImage(step["screenshot"], 100, y - display_height, width=display_width, height=display_height)
                    y -= (display_height + 20)
                except Exception as e:
                    c.drawString(100, y, f"[Error loading screenshot: {e}]")
                    y -= 20
            
            # Render Browser Logs
            if "logs" in step:
                c.setFont("Courier", 8)
                c.drawString(70, y, "Captured Logs:")
                y -= 10
                for log in step["logs"][-10:]: # Show last 10 logs
                    if y < 50:
                        c.showPage()
                        y = height - 50
                    # Sanitize log line to avoid PDF errors
                    safe_log = log.encode('latin-1', 'replace').decode('latin-1')
                    c.drawString(80, y, safe_log[:100])
                    y -= 10
                y -= 10
            
            # Render Security Findings
            if "security_findings" in step:
                c.setFont("Helvetica-Bold", 11)
                c.setFillColorRGB(0.8, 0, 0) # Red color
                c.drawString(70, y, "Security Insights (Passive Scan):")
                c.setFillColorRGB(0, 0, 0) # Reset color
                y -= 15
                # Calculate summary
                counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Info": 0}
                for f in step["security_findings"]:
                    sev = f.get('severity', 'Info')
                    counts[sev] = counts.get(sev, 0) + 1
                
                summary_text = f"Summary: Critical: {counts['Critical']}, High: {counts['High']}, Medium: {counts['Medium']}, Low: {counts['Low']}"
                c.setFont("Helvetica-Oblique", 10)
                c.drawString(70, y, summary_text)
                y -= 20
                
                c.setFont("Helvetica", 9)
                
                for finding in step["security_findings"]:
                    if y < 60:
                        c.showPage()
                        y = height - 50
                    
                    severity = finding.get('severity', 'Info')
                    title = finding.get('type', 'Finding')
                    details = finding.get('details', '')
                    remediation = finding.get('remediation', '')
                    
                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(80, y, f"[{severity}] {title}")
                    y -= 12
                    c.setFont("Helvetica", 9)
                    c.drawString(90, y, f"Details: {details}")
                    y -= 12
                    c.setFont("Helvetica-Oblique", 8)
                    c.drawString(90, y, f"Remediation: {remediation}")
                    y -= 20

            y -= 10
            
        c.save()
        print(f"Report generated: {filename}")
