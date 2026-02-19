from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as PlatypusImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os
from datetime import datetime

class TestReporter:
    def __init__(self, filename="test_report.pdf"):
        self.filename = filename
        self.steps = []
        self.security_findings = []
        self.start_time = datetime.now()

    def add_step(self, description: str, status: str = "INFO", screenshot_path: str = None):
        """Logs a step in the report."""
        self.steps.append({
            "timestamp": datetime.now(),
            "description": description,
            "status": status,
            "screenshot": screenshot_path,
            "security_findings": [] 
        })

    def log_security_finding(self, findings: list):
        """Logs security findings (list of dicts)."""
        if findings:
            # Associate with the last step if possible, otherwise global list
            if self.steps:
                self.steps[-1]["security_findings"].extend(findings)
            else:
                self.security_findings.extend(findings)

    def generate_report(self, filename=None):
        target_file = filename or self.filename
        # Ensure directory exists
        os.makedirs(os.path.dirname(target_file) or ".", exist_ok=True)
        
        doc = SimpleDocTemplate(target_file, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Styles
        title_style = styles['Title']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        code_style = styles['Code']

        # Title
        story.append(Paragraph("Quantum QE Agent Report", title_style))
        story.append(Spacer(1, 12))
        
        # Timestamp
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        story.append(Spacer(1, 12))

        # --- Section 1: Functional Test Log ---
        story.append(Paragraph("1. Functional Test Log", heading_style))
        story.append(Spacer(1, 6))

        for i, step in enumerate(self.steps):
            # Step Description
            status_color = "black"
            if step['status'] == 'PASS': status_color = "green"
            elif step['status'] == 'FAIL': status_color = "red"
            
            step_text = f"<b>Step {i+1}:</b> {step['description']} (<font color='{status_color}'>{step['status']}</font>)"
            story.append(Paragraph(step_text, normal_style))
            story.append(Paragraph(f"<i>Timestamp: {step['timestamp'].strftime('%H:%M:%S')}</i>", normal_style))
            story.append(Spacer(1, 6))

            # Screenshot
            if step['screenshot']:
                try:
                    # Resizing image to fit width (approx 6 inches)
                    img = PlatypusImage(step['screenshot'], width=4*inch, height=3*inch, kind='proportional')
                    story.append(img)
                    story.append(Spacer(1, 6))
                except Exception as e:
                    story.append(Paragraph(f"<i>(Screenshot missing or invalid: {e})</i>", normal_style))
            
            # Security Findings for this step
            if step.get("security_findings"):
                story.append(Paragraph("<b>Security Insights (Passive Scan):</b>", normal_style))
                
                for finding in step["security_findings"]:
                    severity = finding.get('severity', 'Info')
                    sev_color = "black"
                    if severity == 'Critical': sev_color = "red"
                    elif severity == 'High': sev_color = "orange"
                    
                    title = finding.get('type', 'Finding')
                    details = finding.get('details', '')
                    remediation = finding.get('remediation', '')
                    
                    finding_text = f"[{severity}] {title}: {details}"
                    story.append(Paragraph(f"<font color='{sev_color}'>{finding_text}</font>", normal_style))
                    if remediation:
                         story.append(Paragraph(f"<i>Remediation: {remediation}</i>", normal_style))
                    story.append(Spacer(1, 4))

            story.append(Spacer(1, 12))
            
        # --- Section 2: Global Security Findings (if any unattached) ---
        if self.security_findings:
            story.append(Paragraph("2. General Security Findings", heading_style))
            for finding in self.security_findings:
                 severity = finding.get('severity', 'Info')
                 title = finding.get('type', 'Finding')
                 details = finding.get('details', '')
                 story.append(Paragraph(f"[{severity}] {title}: {details}", normal_style))
                 story.append(Spacer(1, 4))

        try:
            doc.build(story)
            print(f"Report generated: {target_file}")
        except Exception as e:
            print(f"Failed to generate report: {e}")
