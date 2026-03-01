import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from src.quantum_qe_core.skills.reporter import TestReporter

class ReporterAgent:
    def __init__(self, reporter: TestReporter):
        self.reporter = reporter
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    async def run(self, job_id: str) -> str:
        """
        Consumes the TestReporter data, uses LangChain to write a Spanish summary,
        and generates the final HTML report.
        """
        # 1. Prepare Data
        steps_list = []
        for i, step in enumerate(self.reporter.steps):
            steps_list.append({
                "step_number": i + 1,
                "description": step.get("description"),
                "status": step.get("status"),
                "security_findings": step.get("security_findings", [])
            })

        data_payload = {
            "total_steps": len(self.reporter.steps),
            "steps": steps_list,
            "general_security_findings": self.reporter.security_findings
        }

        payload_json = json.dumps(data_payload, indent=2)

        # 2. Craft the Prompt
        prompt = PromptTemplate.from_template(
            "Eres el Agente 'Reporter' (Auditor Principal) en un sistema Enterprise de Quality Engineering."
            "Se te proporcionará un JSON con los resultados de la ejecución de una misión de pruebas funcionales y de seguridad.\n\n"
            "Tu tarea es generar un informe ejecutivo de máximo 300 palabras en **Español** dirigido a stakeholders técnicos y de negocio.\n"
            "El informe debe:\n"
            "1. Dar un resumen paso a paso brillante, claro y profesional de lo que ocurrió (mencionando accesos o validaciones destacadas).\n"
            "2. Proporcionar una Conclusión Final sobre la calidad funcional y el estado de seguridad.\n"
            "3. Estar maquetado **ESTRICTAMENTE en HTML** (solo fragmentos, sin <html> ni <body>, ya que se inyectará en una página existente).\n"
            "4. Usar las siguientes clases de Tailwind CSS para mantener el diseño corporativo Light-Mode:\n"
            "   - Textos normales: `text-[#060b29] text-sm`\n"
            "   - Títulos internos: `text-lg font-bold text-[#03287d] mb-2`\n"
            "   - Acentos o badges: `bg-[#e0e7ff] text-[#0032a7] px-2 py-1 rounded font-bold`\n"
            "   - Alertas/Problemas: `bg-red-50 text-red-700 border-l-4 border-red-500 p-2`\n"
            "   - Éxitos: `bg-green-50 text-green-700 border-l-4 border-green-500 p-2`\n\n"
            "### JSON DE EJECUCIÓN:\n"
            "{payload}\n\n"
            "Devuelve SOLO el código HTML, sin bloques de código Markdown."
        )

        chain = prompt | self.llm

        try:
            print("[ReporterAgent] Generating Spanish Execution Summary via LLM...")
            result = await chain.ainvoke({"payload": payload_json})
            spanish_summary_html = result.content.strip()
            
            # Remove Markdown block wrappers if the LLM hallucinated them
            if spanish_summary_html.startswith("```html"):
                spanish_summary_html = spanish_summary_html[7:]
            if spanish_summary_html.endswith("```"):
                spanish_summary_html = spanish_summary_html[:-3]

        except Exception as e:
            print(f"[ReporterAgent] Failed to generate summary: {e}")
            spanish_summary_html = "<div class='p-4 bg-red-100 text-red-700'>Error al generar resumen IA.</div>"

        # 3. Generate the Final Report
        # Ensure 'output' directory exists since generate_html_report saves there
        os.makedirs("output", exist_ok=True)
        self.reporter.generate_html_report(job_id=job_id, spanish_summary=spanish_summary_html)
        
        # Output filename expected by the reporter method
        html_filename = f"output/report_{job_id}.html"
        return html_filename
