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

    def generate_html_report(self, job_id: str, spanish_summary: str = "", agents_executed: list = None, telemetry_data: dict = None):
        """Generates a professional HTML report with Tailwind CSS and Chart.js."""
        agents_executed = agents_executed or ["functional"]
        telemetry_data = telemetry_data or {}
        html_filename = f"output/report_{job_id}.html"
        os.makedirs("output", exist_ok=True)

        # Calculate Metrics
        total_steps = len(self.steps)
        passed_steps = sum(1 for s in self.steps if s['status'] == 'PASS')
        failed_steps = total_steps - passed_steps
        
        # Collect all findings (global + step-specific)
        all_findings = self.security_findings.copy()
        for step in self.steps:
            all_findings.extend(step.get('security_findings', []))
            
        total_vulns = len(all_findings)
        severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Info': 0}
        
        # Categorize findings for the report
        passive_findings = []
        active_findings = []
        
        for f in all_findings:
            sev = f.get('severity', 'Info')
            if sev in severity_counts:
                severity_counts[sev] += 1
            else:
                severity_counts['Info'] += 1
            
            # Simple heuristic for categorization if not explicitly typed
            f_type = f.get('type', '').lower()
            if "header" in f_type or "cookie" in f_type:
                passive_findings.append(f)
            else:
                active_findings.append(f)

        # HTML Content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQASA Enterprise QA Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
    </style>
</head>
<body class="bg-[#f3f4f6] text-[#060b29]">

    <!-- Navbar -->
    <nav class="bg-[#03287d] text-white p-4 shadow-lg border-b-4 border-[#ffc440]">
        <div class="container mx-auto flex justify-between items-center">
            <div class="flex items-center gap-2">
                <span class="text-2xl font-black tracking-tight">SQASA | Enterprise QA</span>
                <span class="px-2 py-0.5 rounded bg-[#0032a7] text-xs font-mono font-bold">Report v1.0</span>
            </div>
            <div class="text-sm font-mono text-gray-300">Execution ID: {job_id}</div>
        </div>
    </nav>

    <div class="container mx-auto p-6 max-w-7xl">
        
        <!-- Executive Summary -->
        <h2 class="text-xl font-black text-[#03287d] mb-4 border-l-4 border-[#fca311] pl-3 uppercase tracking-wider">Executive Summary</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <div class="text-gray-500 text-xs font-bold uppercase tracking-wide">Total Steps</div>
                <div class="text-4xl font-black text-[#03287d] mt-2">{total_steps}</div>
            </div>
             <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <div class="text-gray-500 text-xs font-bold uppercase tracking-wide">Functional Pass Rate</div>
                <div class="flex items-baseline gap-2 mt-2">
                     <div class="text-4xl font-black text-[#0032a7]">{passed_steps}</div>
                     <span class="text-sm text-gray-400 font-bold">/ {total_steps}</span>
                </div>
            </div>
             <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <div class="text-gray-500 text-xs font-bold uppercase tracking-wide">Security Vulnerabilities</div>
                <div class="text-4xl font-black text-[#fca311] mt-2">{total_vulns}</div>
            </div>
             <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <div class="text-gray-500 text-xs font-bold uppercase tracking-wide">Critical Issues</div>
                <div class="text-4xl font-black text-red-600 mt-2">{severity_counts['Critical']}</div>
            </div>
        </div>

        <!-- Charts Section -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
            <div class="bg-white p-6 rounded-xl shadow-md border border-gray-200">
                <h3 class="text-sm font-bold text-[#03287d] uppercase mb-4 tracking-wider">Functional Execution Status</h3>
                <div class="h-64 flex justify-center">
                    <canvas id="functionalChart"></canvas>
                </div>
            </div>
            <div class="bg-white p-6 rounded-xl shadow-md border border-gray-200">
                <h3 class="text-sm font-bold text-[#03287d] uppercase mb-4 tracking-wider">Vulnerability Severity Distribution</h3>
                <div class="h-64 flex justify-center">
                    <canvas id="securityChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Section 2: Security Audit Report -->
        <h2 class="text-xl font-black text-[#03287d] mb-6 border-l-4 border-[#ffc440] pl-3 uppercase tracking-wider">Security Audit Report</h2>
"""
        if "security" not in agents_executed:
            html_content += """
        <div class="bg-gray-100 border border-gray-300 rounded-lg p-6 text-center text-gray-500 font-bold mb-12 shadow-sm">
            Agente Security Auditor no ejecutado para esta misión
        </div>
"""
        else:
            html_content += """
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
            <!-- Passive Scan Column -->
            <div>
                <div class="flex items-center gap-2 mb-4">
                     <span class="w-8 h-8 rounded-full bg-[#03287d]/10 flex items-center justify-center text-[#03287d] font-bold text-sm">P</span>
                     <h3 class="text-lg font-bold text-[#060b29]">Passive Analysis</h3>
                </div>
                <div class="space-y-4">
"""
        
        # Render Passive Findings
        if not passive_findings:
             html_content += '<div class="p-4 bg-green-50 text-green-700 rounded text-sm text-center">No passive vulnerabilities detected.</div>'
        else:
            for f in passive_findings:
                sev_color = "bg-gray-100 text-gray-800"
                if f.get('severity') == 'Critical': sev_color = "bg-red-100 text-red-800 border-red-200"
                elif f.get('severity') == 'High': sev_color = "bg-orange-100 text-orange-800 border-orange-200"
                elif f.get('severity') == 'Medium': sev_color = "bg-yellow-100 text-yellow-800 border-yellow-200"
                
                cwe_badge = f"<span class='ml-2 text-xs font-mono text-gray-400'>{f.get('cwe', '')}</span>" if f.get('cwe') else ""

                html_content += f"""
                <div class="bg-white rounded border border-gray-200 shadow-sm p-4 hover:shadow-md transition">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex flex-col">
                            <span class="font-bold text-gray-800 text-sm">{f.get('type')}</span>
                            {cwe_badge}
                        </div>
                        <span class="px-2 py-0.5 rounded text-xs font-bold {sev_color}">{f.get('severity')}</span>
                    </div>
                    <p class="text-xs text-gray-600 mb-2">{f.get('details')}</p>
                    <div class="bg-gray-50 p-2 rounded text-xs text-gray-500 font-mono border border-gray-100">
                        fix: {f.get('remediation')}
                    </div>
                </div>
                """

        html_content += """
                </div>
            </div>

            <!-- Active Scan Column -->
             <div>
                <div class="flex items-center gap-2 mb-4">
                     <span class="w-8 h-8 rounded-full bg-[#fca311]/10 flex items-center justify-center text-[#fca311] font-bold text-sm">A</span>
                     <h3 class="text-lg font-bold text-[#060b29]">Active Scanning</h3>
                </div>
                <div class="space-y-4">
        """

        # Render Active Findings
        if not active_findings:
             html_content += '<div class="p-4 bg-green-50 text-green-700 rounded text-sm text-center">No active vulnerabilities detected.</div>'
        else:
            for f in active_findings:
                sev_color = "bg-gray-100 text-gray-800"
                if f.get('severity') == 'Critical': sev_color = "bg-red-100 text-red-800 border-red-200"
                elif f.get('severity') == 'High': sev_color = "bg-orange-100 text-orange-800 border-orange-200"
                elif f.get('severity') == 'Medium': sev_color = "bg-yellow-100 text-yellow-800 border-yellow-200"

                cwe_badge = f"<span class='ml-2 text-xs font-mono text-gray-400'>{f.get('cwe', '')}</span>" if f.get('cwe') else ""

                html_content += f"""
                <div class="bg-white rounded border border-gray-200 shadow-sm p-4 hover:shadow-md transition">
                    <div class="flex justify-between items-start mb-2">
                         <div class="flex flex-col">
                            <span class="font-bold text-gray-800 text-sm">{f.get('type')}</span>
                            {cwe_badge}
                        </div>
                        <span class="px-2 py-0.5 rounded text-xs font-bold {sev_color}">{f.get('severity')}</span>
                    </div>
                    <p class="text-xs text-gray-600 mb-2">{f.get('details')}</p>
                    <div class="bg-gray-50 p-2 rounded text-xs text-gray-500 font-mono border border-gray-100">
                        fix: {f.get('remediation')}
                    </div>
                </div>
                """

        html_content += """
                </div>
            </div>
        </div>
"""
        
        # Synthetic Data Section
        html_content += """
        <!-- Section 2.5: Synthetic Data -->
        <h2 class="text-xl font-black text-[#03287d] mb-6 border-l-4 border-purple-500 pl-3 uppercase tracking-wider">Synthetic Data Agent</h2>
"""
        if "synthetic" not in agents_executed:
            html_content += """
        <div class="bg-gray-100 border border-gray-300 rounded-lg p-6 text-center text-gray-500 font-bold mb-12 shadow-sm">
            Agente Synthetic Data no ejecutado para esta misión
        </div>
"""
        else:
            html_content += """
        <div class="bg-white border border-gray-200 shadow-sm p-6 rounded-lg mb-12">
            <p class="text-sm text-gray-600">El agente de datos sintéticos generó datos de prueba enrutados a los campos del formulario durante la ejecución.</p>
        </div>
"""

        # Telemetry Section
        html_content += """
        <!-- Section 2.8: Telemetry Data -->
        <h2 class="text-xl font-black text-[#03287d] mb-6 border-l-4 border-cyan-500 pl-3 uppercase tracking-wider">Telemetry & Cost Observatory</h2>
        <div class="grid grid-cols-3 gap-4 mb-12">
"""
        if not telemetry_data:
            html_content += """
            <div class="col-span-3 bg-gray-100 border border-gray-300 rounded-lg p-6 text-center text-gray-500 font-bold shadow-sm">
                Agente Telemetry no ejecutado para esta misión
            </div>
            """
        else:
            html_content += f"""
            <div class="bg-white border border-gray-200 shadow-sm p-4 rounded-lg text-center">
                <div class="text-xs text-gray-500 font-bold uppercase">LLM Tokens</div>
                <div class="text-2xl font-black text-[#0032a7]">{telemetry_data.get('tokens', 0):,}</div>
            </div>
            <div class="bg-white border border-gray-200 shadow-sm p-4 rounded-lg text-center">
                <div class="text-xs text-gray-500 font-bold uppercase">Estimated Cost</div>
                <div class="text-2xl font-black text-green-600">${telemetry_data.get('cost', 0.0):.4f}</div>
            </div>
            <div class="bg-white border border-gray-200 shadow-sm p-4 rounded-lg text-center">
                <div class="text-xs text-gray-500 font-bold uppercase">Bandwidth</div>
                <div class="text-2xl font-black text-purple-600">{telemetry_data.get('network_mb', 0.0):.2f} MB</div>
            </div>
            """
        html_content += """
        </div>

        <!-- Section 3: Functional Execution Log -->
        <h2 class="text-xl font-black text-[#03287d] mb-6 border-l-4 border-[#0032a7] pl-3 uppercase tracking-wider">Functional Execution Log</h2>
        <div class="space-y-4 mb-12">
"""
        
        # Render Steps
        for i, step in enumerate(self.steps):
            status_color = "text-green-700 bg-green-50 border-green-200" if step['status'] == 'PASS' else "text-red-700 bg-red-50 border-red-200"
            border_left = "border-l-4 border-green-500" if step['status'] == 'PASS' else "border-l-4 border-red-500"
            
            # Image handling
            img_html = ""
            if step['screenshot']:
                # The browser saves screenshots to output/report_screenshots/...
                # The HTML is in output/..., so we need relative path 'report_screenshots/...'
                rel_path = step['screenshot'].replace("output/", "").replace("output\\", "")
                img_html = f"""
                <div class="mt-3 border-t pt-3">
                    <p class="text-[10px] uppercase font-bold text-gray-400 mb-2 tracking-wider">Screen Capture</p>
                    <a href="{rel_path}" target="_blank">
                        <img src="{rel_path}" class="rounded border shadow-sm w-48 hover:w-full hover:max-w-2xl transition-all duration-300" alt="Step Screenshot">
                    </a>
                </div>
                """

            html_content += f"""
            <div class="bg-white rounded shadow-sm border border-gray-200 overflow-hidden {border_left}">
                <div class="p-4">
                    <div class="flex items-center justify-between mb-2">
                         <div class="flex items-center gap-3">
                            <span class="w-6 h-6 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center text-xs font-bold font-mono">{i+1}</span>
                            <span class="text-xs font-mono text-gray-400">{step['timestamp'].strftime('%H:%M:%S')}</span>
                         </div>
                         <span class="px-2 py-0.5 rounded text-xs font-bold border {status_color}">{step['status']}</span>
                    </div>
                    <p class="text-gray-800 text-sm font-medium leading-relaxed">{step['description']}</p>
                    {img_html}
                </div>
            </div>
            """

        html_content += """
        </div>

        <!-- Section 4: AI Agent Step-by-Step Summary & Conclusion (Spanish) -->
        <h2 class="text-xl font-black text-[#03287d] mb-6 border-l-4 border-green-500 pl-3 uppercase tracking-wider">Resumen y Conclusiones del Agente</h2>
        <div class="bg-white p-8 rounded-xl shadow-md border border-gray-200 mb-20">
            %s
        </div>
        
        <script>
            // Charts Configuration
            const functionalCtx = document.getElementById('functionalChart').getContext('2d');
            new Chart(functionalCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Passed', 'Failed'],
                    datasets: [{
                        data: [%d, %d],
                        backgroundColor: ['#0032a7', '#EF4444'], // Royal Blue & Red
                        borderWidth: 0
                    }]
                },
                options: { cutout: '75%%', responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } } } }
            });

            const securityCtx = document.getElementById('securityChart').getContext('2d');
            new Chart(securityCtx, {
                type: 'bar',
                data: {
                    labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
                    datasets: [{
                        label: 'Findings',
                        data: [%d, %d, %d, %d, %d],
                        backgroundColor: ['#DC2626', '#fca311', '#ffc440', '#3B82F6', '#9CA3AF'], // Red, Orange, Gold, Blue, Gray
                        borderRadius: 4,
                        maxBarThickness: 30
                    }]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false,
                    scales: { 
                        y: { beginAtZero: true, grid: { display: true, drawBorder: false }, ticks: { stepSize: 1 } },
                        x: { grid: { display: false } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        </script>
    </div>
    <div class="bg-[#03287d] text-white py-12 mt-12 border-t-4 border-[#ffc440]">
        <div class="container mx-auto text-center">
            <h3 class="font-black text-xl mb-2 tracking-wider">SQASA ENTERPRISE</h3>
            <p class="text-blue-200 text-sm font-bold uppercase tracking-widest">Automated Functional & Security Assurance</p>
        </div>
    </div>
</body>
</html>
        """ % (spanish_summary or "<p class='text-gray-500 italic'>Sin resumen generado.</p>", passed_steps, failed_steps, 
               severity_counts['Critical'], severity_counts['High'], 
               severity_counts['Medium'], severity_counts['Low'], severity_counts['Info'])

        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"HTML Report generated: {html_filename}")
