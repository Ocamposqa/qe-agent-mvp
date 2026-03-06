"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Square, Activity, ShieldAlert, CheckCircle2, Terminal as TerminalIcon, Eye, Globe, MessageSquare, Send } from "lucide-react";

const AVAILABLE_AGENTS = [
  { id: "ui", name: "UI Verifier Agent", icon: Eye },
  { id: "functional", name: "Functional Agent", icon: Activity },
  { id: "synthetic", name: "Synthetic Data Agent", icon: Globe },
  { id: "security", name: "Security Auditor", icon: ShieldAlert },
];

export default function CorporateQEDashboard() {
  const [url, setUrl] = useState("https://sqasa.co/contacto");
  const [instructions, setInstructions] = useState("Llena el campo de email con test@qa.com y presiona enviar. Verifica el mensaje de exito y detente.");
  const [status, setStatus] = useState("Idle"); // Idle, Running, Paused_HITL, Complete, Failed
  const [logs, setLogs] = useState<string[]>([]);
  const [domImage, setDomImage] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [reportUrl, setReportUrl] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [telemetry, setTelemetry] = useState({ tokens: 0, ms: 0 });
  const [selectedAgents, setSelectedAgents] = useState<string[]>(["functional"]);

  // HITL State
  const [hitlPrompt, setHitlPrompt] = useState<string | null>(null);
  const [hitlReply, setHitlReply] = useState("");

  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const toggleAgent = (id: string) => {
    setSelectedAgents(prev => prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id]);
  };

  const startScan = async () => {
    if (selectedAgents.length === 0) {
      alert("Debes seleccionar al menos un agente para la misión.");
      return;
    }
    setStatus("Running");
    setHitlPrompt(null);
    setReportUrl(null);
    setLogs((prev) => [...prev, "[SYSTEM] Iniciando Orquestación Multi-Agente...", `[SYSTEM] Agentes activados: ${selectedAgents.join(", ")}`]);

    try {
      const res = await fetch("http://localhost:8000/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Sending selected agents to the backend (backend implementation pending)
        body: JSON.stringify({ url, instructions, skip_security: !selectedAgents.includes("security"), headless: true, agents: selectedAgents })
      });
      const data = await res.json();

      if (data.job_id) {
        setJobId(data.job_id);
        connectWebSocket(data.job_id);
      }
    } catch (error) {
      setLogs((prev) => [...prev, `[ERROR] Connection failed: ${error}`]);
      setStatus("Failed");
    }
  };

  const connectWebSocket = async (id: string) => {
    try {
      const negotiateData = await fetch(`http://localhost:8000/api/negotiate/${id}`);
      const { url } = await negotiateData.json();

      let socket: WebSocket;
      try {
        socket = new WebSocket(url);
      } catch (wsError) {
        socket = new WebSocket(`ws://localhost:8000/ws/telemetry/${id}`);
      }

      socket.onerror = (error) => {
        if (socket.url !== `ws://localhost:8000/ws/telemetry/${id}`) {
          socket.close();
          const fallbackSocket = new WebSocket(`ws://localhost:8000/ws/telemetry/${id}`);
          setupSocketHandlers(fallbackSocket);
          setWs(fallbackSocket);
        }
      };

      const setupSocketHandlers = (s: WebSocket) => {
        s.onmessage = (event) => {
          const data = JSON.parse(event.data);

          if (data.type === "log") {
            setLogs((prev) => [...prev, `[AGENT] ${data.message}`]);
            setTelemetry(prev => ({ ...prev, tokens: prev.tokens + Math.floor(Math.random() * 200) + 50, ms: prev.ms + 600 }));
          } else if (data.type === "dom_update" && data.image) {
            setDomImage(data.image);
            setTelemetry(prev => ({ ...prev, tokens: prev.tokens + 1500, ms: prev.ms + 1200 }));
          } else if (data.type === "status") {
            setLogs((prev) => [...prev, `[SYSTEM] Status: ${data.phase || data.message}`]);
            if (data.phase === "Complete") {
              setStatus("Complete");
              if (data.html_report_url) setReportUrl(data.html_report_url);
            }
          } else if (data.type === "hitl_request") {
            // New HITL Event
            setStatus("Paused_HITL");
            setHitlPrompt(data.message);
            setLogs((prev) => [...prev, `[SYSTEM] ⚠️ PAUSADO: Agente requiere asistencia humana.`]);
          }
        };
        s.onclose = () => setLogs((prev) => [...prev, "[SYSTEM] Desconectado."]);
      };

      setupSocketHandlers(socket);
      setWs(socket);

    } catch (error) {
      console.error(error);
    }
  };

  const submitHitlReply = async () => {
    if (!hitlReply.trim() || !jobId) return;

    setLogs((prev) => [...prev, `[HUMAN] Respuesta enviada: ${hitlReply}`]);
    setStatus("Running");
    setHitlPrompt(null);

    // Send response via API (assuming a new endpoint /api/hitl_resume)
    try {
      await fetch(`http://localhost:8000/api/hitl_resume/${jobId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reply: hitlReply })
      });
      setHitlReply("");
    } catch (e) {
      setLogs((prev) => [...prev, `[ERROR] No se pudo reanudar el agente.`]);
    }
  };

  // Corporate Light Palette: #03287d (Navy), #FFC440 (Gold), #f3f4f6 (Light Gray BG)
  return (
    <div className="h-screen w-screen flex flex-col p-4 gap-4 overflow-hidden relative bg-[#f3f4f6] text-[#060b29] selection:bg-[#ffc440]/30 font-sans">

      {/* Header */}
      <header className="bg-white shadow border border-gray-200 rounded-xl p-4 flex items-center justify-between z-10">
        <div className="flex items-center gap-4">
          <div className="bg-[#03287d] p-2 rounded-lg text-white">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tight text-[#03287d]">SQASA | <span className="text-gray-500 font-medium">Enterprise QA</span></h1>
            <p className="text-xs text-gray-500 font-medium">Multi-Agent Testing Console</p>
          </div>
        </div>

        <div className="flex gap-4">
          {status === "Complete" && (
            <button
              onClick={() => reportUrl && window.open(reportUrl, "_blank")}
              className="bg-[#ffc440] hover:bg-[#fca311] text-[#060b29] font-bold px-4 py-2 rounded-lg flex items-center gap-2 shadow transition transform hover:scale-105"
            >
              <CheckCircle2 className="w-4 h-4" />
              Open HTML Report
            </button>
          )}
          <div className="bg-gray-50 border border-gray-100 rounded px-4 py-2 flex flex-col items-end">
            <span className="text-[10px] text-gray-400 font-bold uppercase">LLM Tokens</span>
            <span className="font-mono text-[#0032a7] font-bold">{telemetry.tokens.toLocaleString()}</span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0 z-10">

        {/* Left Column: Mission Setup & Console */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-4 min-h-0">

          {/* Controls Panel */}
          <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="bg-white shadow border border-gray-200 rounded-xl p-5 flex flex-col gap-4">

            <h2 className="text-sm font-bold uppercase tracking-wider text-[#03287d] flex items-center gap-2 border-b pb-2">
              <Globe className="w-4 h-4" /> Configuración de Misión
            </h2>

            <div>
              <label className="text-xs font-bold text-gray-500 mb-1 block">URL Objetivo</label>
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-sm text-[#060b29] focus:outline-none focus:border-[#0032a7] focus:ring-1 focus:ring-[#0032a7] transition-colors shadow-sm"
                disabled={status === "Running" || status === "Paused_HITL"}
              />
            </div>

            <div>
              <label className="text-xs font-bold text-gray-500 mb-1 block">Especialistas Tácticos (MAS)</label>
              <div className="grid grid-cols-2 gap-2">
                {AVAILABLE_AGENTS.map((agent) => {
                  const isSelected = selectedAgents.includes(agent.id);
                  const Icon = agent.icon;
                  return (
                    <button
                      key={agent.id}
                      onClick={() => toggleAgent(agent.id)}
                      disabled={status !== "Idle" && status !== "Complete" && status !== "Failed"}
                      className={`flex items-center gap-2 px-3 py-2 rounded-md border text-xs font-semibold transition-all ${isSelected ? 'bg-[#03287d] text-white border-[#03287d]' : 'bg-gray-50 text-gray-600 border-gray-200 hover:border-[#0032a7]'}`}
                    >
                      <Icon className="w-3 h-3" />
                      {agent.name}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-gray-500 mb-1 block">Directivas Funcionales (Prompt)</label>
              <textarea
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-sm text-[#060b29] h-20 resize-none focus:outline-none focus:border-[#0032a7] focus:ring-1 focus:ring-[#0032a7] shadow-sm"
                disabled={status === "Running" || status === "Paused_HITL"}
              />
            </div>

            <button
              onClick={startScan}
              disabled={status === "Running" || status === "Paused_HITL"}
              className="w-full bg-[#03287d] hover:bg-[#0032a7] disabled:bg-gray-300 disabled:text-gray-500 text-white font-bold py-3 rounded-lg shadow-md transition-all flex items-center justify-center gap-2"
            >
              {status === "Running" ? <Square className="w-5 h-5 animate-pulse" /> : <Play className="w-5 h-5" />}
              {status === "Running" ? "ORQUESTANDO..." : status === "Paused_HITL" ? "MISION PAUSADA" : "EJECUTAR MISIÓN"}
            </button>
          </motion.div>

          {/* Telemetry Log */}
          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }} className="bg-[#060b29] rounded-xl flex flex-col flex-1 min-h-0 border border-gray-800 shadow-inner">
            <div className="bg-black/30 px-4 py-2 border-b border-white/10 flex items-center gap-2">
              <TerminalIcon className="w-4 h-4 text-[#ffc440]" />
              <span className="text-xs font-mono font-bold text-[#ffc440] tracking-wider">LIVE_TELEMETRY</span>
            </div>
            <div className="flex-1 p-4 overflow-y-auto terminal-scroll font-mono text-xs flex flex-col gap-1">
              {logs.length === 0 ? (
                <span className="text-gray-500">Esperando comandos de lanzamiento...</span>
              ) : (
                logs.map((log, i) => (
                  <span key={i} className={
                    log.includes("[ERROR]") ? "text-red-400" :
                      log.includes("[HUMAN]") ? "text-[#ffc440] font-bold" :
                        log.includes("[SECURITY]") ? "text-orange-400" :
                          log.includes("[SYSTEM]") ? "text-cyan-300 font-bold" : "text-gray-300"
                  }>
                    <span className="text-gray-600/[0.5]">[{new Date().toLocaleTimeString()}]</span> {log}
                  </span>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </motion.div>
        </div>

        {/* Right Column: Mission View & HITL */}
        <div className="col-span-12 lg:col-span-8 flex flex-col min-h-0 gap-4">

          {/* Progress / Status Bar */}
          <div className="bg-white rounded-xl shadow border border-gray-200 p-4 flex items-center justify-between">
            <div className="flex items-center gap-3 w-1/2">
              <div className="text-sm font-bold text-gray-500 uppercase">Estado:</div>
              <div className={`text-sm font-black uppercase ${status === "Running" ? "text-[#0032a7]" : status === "Paused_HITL" ? "text-[#fca311] animate-pulse" : "text-gray-800"}`}>
                {status}
              </div>
            </div>
            <div className="w-1/2 bg-gray-100 rounded-full h-2.5 overflow-hidden">
              <div className={`h-full rounded-full transition-all duration-500 ${status === "Complete" ? "bg-green-500 w-full" : status === "Running" ? "bg-[#03287d] w-1/2 animate-pulse" : status === "Paused_HITL" ? "bg-[#ffc440] w-1/2" : "bg-gray-300 w-0"}`}></div>
            </div>
          </div>

          <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }} className="bg-white rounded-xl shadow border border-gray-200 flex flex-col flex-1 min-h-0 relative overflow-hidden">

            {/* Image Viewer */}
            <div className={`flex-1 flex items-center justify-center p-4 overflow-hidden ${status === "Paused_HITL" ? "pb-32" : ""}`}>
              <AnimatePresence mode="wait">
                {domImage ? (
                  <motion.img
                    key={domImage.substring(0, 20)}
                    initial={{ opacity: 0, scale: 1.05 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    src={`data:image/jpeg;base64,${domImage}`}
                    className={`max-w-full max-h-full object-contain rounded shadow-lg border border-gray-100 transition-all ${status === "Paused_HITL" ? "grayscale blur-sm" : ""}`}
                    alt="Agent View"
                  />
                ) : (
                  <div className="flex flex-col items-center gap-4 text-gray-300">
                    <Globe className="w-16 h-16" />
                    <p className="font-bold uppercase tracking-widest text-sm">SIN SEÑAL VISUAL</p>
                  </div>
                )}
              </AnimatePresence>
            </div>

            {/* Human-In-The-Loop Chat Overlay */}
            <AnimatePresence>
              {status === "Paused_HITL" && (
                <motion.div
                  initial={{ y: 100, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: 100, opacity: 0 }}
                  className="absolute bottom-0 left-0 w-full bg-white border-t-2 border-[#ffc440] shadow-[0_-10px_40px_rgba(0,0,0,0.1)] p-6"
                >
                  <div className="max-w-3xl mx-auto flex flex-col gap-3">
                    <div className="flex items-center gap-2 text-[#03287d] font-bold">
                      <MessageSquare className="w-5 h-5 text-[#fca311]" />
                      Atención Requerida por el Agente
                    </div>
                    <p className="text-gray-700 font-medium bg-[#ffc440]/10 border border-[#ffc440]/30 p-3 rounded-lg">
                      "{hitlPrompt || "El agente no está seguro de cómo proceder o le falta información. Por favor, asístelo."}"
                    </p>

                    <div className="flex gap-2 mt-2">
                      <input
                        value={hitlReply}
                        onChange={(e) => setHitlReply(e.target.value)}
                        placeholder="Escribe tu respuesta o instrucción explícita..."
                        className="flex-1 bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#03287d]"
                        onKeyDown={(e) => e.key === 'Enter' && submitHitlReply()}
                      />
                      <button
                        onClick={submitHitlReply}
                        className="bg-[#03287d] hover:bg-[#0032a7] text-white px-6 py-2 rounded-lg font-bold flex items-center gap-2 shadow"
                      >
                        Responder <Send className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

          </motion.div>
        </div>

      </div>
    </div>
  );
}
