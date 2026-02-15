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

    def generate_report(self):
        """Generates the PDF report."""
        c = canvas.Canvas(self.filename, pagesize=letter)
        width, height = letter
        y = height - 50

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, f"QE Agent Test Report")
        y -= 25
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        y -= 40

        # Steps
        for step in self.steps:
            if y < 100: # New page if running out of space
                c.showPage()
                y = height - 50
            
            # Step Text
            c.setFont("Helvetica-Bold", 10)
            status_color = (0, 0.5, 0) if step["status"] == "PASS" else (1, 0, 0) if step["status"] == "FAIL" else (0, 0, 0)
            c.setFillColorRGB(*status_color)
            c.drawString(50, y, f"[{step['status']}]")
            c.setFillColorRGB(0, 0, 0)
            
            c.setFont("Helvetica", 10)
            c.drawString(100, y, f"{step['timestamp'].strftime('%H:%M:%S')} - {step['description']}")
            y -= 20

            # Screenshot
            if step["screenshot"] and os.path.exists(step["screenshot"]):
                try:
                    # Resize image to fit width while maintaining aspect ratio
                    img = ImageReader(step["screenshot"])
                    img_width, img_height = img.getSize()
                    aspect = img_height / float(img_width)
                    
                    display_width = 400
                    display_height = display_width * aspect
                    
                    if y - display_height < 50:
                        c.showPage()
                        y = height - 50
                    
                    c.drawImage(step["screenshot"], 100, y - display_height, width=display_width, height=display_height)
                    y -= (display_height + 20)
                except Exception as e:
                    c.drawString(100, y, f"[Error loading screenshot: {e}]")
                    y -= 20
            
            y -= 10 # Extra spacing between steps

        c.save()
        print(f"Report generated: {self.filename}")
