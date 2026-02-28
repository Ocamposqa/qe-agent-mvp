"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Square, Activity, ShieldAlert, CheckCircle2, Terminal as TerminalIcon, Eye, Globe } from "lucide-react";

export default function QuantumDashboard() {
  const [url, setUrl] = useState("http://localhost:3000");
  const [instructions, setInstructions] = useState("Login and verify basic functionalities.");
  const [status, setStatus] = useState("Idle"); // Idle, Running, Complete, Failed
  const [logs, setLogs] = useState<string[]>([]);
  const [domImage, setDomImage] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [telemetry, setTelemetry] = useState({ tokens: 0, ms: 0 });

  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const startScan = async () => {
    setStatus("Running");
    setLogs((prev) => [...prev, "[SYSTEM] Initiating Quantum Core Orchestration..."]);

    try {
      const res = await fetch("http://localhost:8000/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, instructions, skip_security: false, headless: true })
      });
      const data = await res.json();
      console.log("Job initialized:", data);

      if (data.job_id) {
        setJobId(data.job_id);
        connectWebSocket(data.job_id);
      }
    } catch (error) {
      setLogs((prev) => [...prev, `[ERROR] Failed to connect to API: ${error}`]);
      setStatus("Failed");
    }
  };

  const connectWebSocket = async (id: string) => {
    try {
      // 1. Negotiate with backend to get the Azure Web PubSub temporary URL
      const negotiateData = await fetch(`http://localhost:8000/api/negotiate/${id}`);
      const { url } = await negotiateData.json();

      // 2. Connect to Azure Web PubSub (or fallback to local mock if Azure fails)
      let socket: WebSocket;
      try {
        socket = new WebSocket(url);
      } catch (wsError) {
        console.warn("Primary WebSocket failed, attempting local fallback...", wsError);
        socket = new WebSocket(`ws://localhost:8000/ws/telemetry/${id}`);
      }

      socket.onerror = (error) => {
        console.warn("WebSocket error. Attempting fallback if not already using it.", error);
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
            setLogs((prev) => [...prev, `[SYSTEM] Status change: ${data.phase || data.message}`]);
            if (data.phase === "Complete") setStatus("Complete");
          } else if (data.type === "security_findings") {
            setLogs((prev) => [...prev, `[SECURITY] Audit complete. Found ${data.findings_count} vulnerabilities.`]);
          }
        };

        s.onclose = () => setLogs((prev) => [...prev, "[SYSTEM] Telemetry stream disconnected."]);
      };

      setupSocketHandlers(socket);
      setWs(socket);

    } catch (error) {
      console.error("Failed to connect to pubsub", error);
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col p-4 gap-4 overflow-hidden relative selection:bg-cyan-500/30">
      {/* Header */}
      <header className="glass-panel rounded-xl p-4 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Activity className="text-cyan-400 w-8 h-8" />
            {status === "Running" && (
              <span className="absolute top-0 left-0 w-full h-full animate-ping opacity-50 text-cyan-400 rounded-full bg-cyan-400"></span>
            )}
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-widest text-white uppercase shadow-cyan-500 text-shadow">Quantum QE Pilot</h1>
            <p className="text-xs text-cyan-200/50 font-mono">Enterprise Nexus v1.0</p>
          </div>
        </div>

        <div className="flex gap-4">
          <div className="glass-panel rounded px-4 py-2 flex flex-col items-end">
            <span className="text-[10px] text-gray-400 uppercase tracking-wider font-bold">LLM Tokens</span>
            <span className="font-mono text-purple-400 font-bold">{telemetry.tokens.toLocaleString()}</span>
          </div>
          <div className="glass-panel rounded px-4 py-2 flex flex-col items-end">
            <span className="text-[10px] text-gray-400 uppercase tracking-wider font-bold">Billing Est.</span>
            <span className="font-mono text-green-400 font-bold">${((telemetry.tokens / 1000) * 0.01).toFixed(4)}</span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0 z-10">

        {/* Left Column: Controls & Terminal */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-4 min-h-0">

          {/* Controls */}
          <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="glass-panel rounded-xl p-5 flex flex-col gap-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
              <Globe className="w-4 h-4" /> Mission Target
            </h2>

            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-sm text-cyan-100 font-mono focus:outline-none focus:border-cyan-500 transition-colors"
              placeholder="Target URL"
              disabled={status === "Running"}
            />

            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-sm text-gray-200 font-mono h-24 resize-none focus:outline-none focus:border-cyan-500 transition-colors"
              placeholder="Directives..."
              disabled={status === "Running"}
            />

            <button
              onClick={startScan}
              disabled={status === "Running"}
              className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-800 disabled:text-gray-500 text-white font-bold py-3 rounded transition-all flex items-center justify-center gap-2"
            >
              {status === "Running" ? <Square className="w-5 h-5 animate-pulse" /> : <Play className="w-5 h-5" />}
              {status === "Running" ? "ABORT MISSION" : "ENGAGE AUTOPILOT"}
            </button>
          </motion.div>

          {/* Terminal */}
          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }} className="glass-panel rounded-xl p-0 flex flex-col flex-1 min-h-0 border-t-2 border-t-cyan-500">
            <div className="bg-black/40 px-4 py-2 border-b border-white/5 flex items-center gap-2">
              <TerminalIcon className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono font-bold text-gray-300 tracking-wider">AGENT_TELEMETRY</span>
            </div>
            <div className="flex-1 p-4 overflow-y-auto terminal-scroll font-mono text-xs flex flex-col gap-1">
              {logs.length === 0 ? (
                <span className="text-gray-600">Awaiting dispatch orders...</span>
              ) : (
                logs.map((log, i) => (
                  <span key={i} className={
                    log.includes("[ERROR]") ? "text-red-400" :
                      log.includes("[SECURITY]") ? "text-orange-400" :
                        log.includes("[SYSTEM]") ? "text-cyan-300" : "text-gray-300"
                  }>
                    <span className="text-gray-600">[{new Date().toLocaleTimeString()}]</span> {log}
                  </span>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </motion.div>
        </div>

        {/* Right Column: HUD View (Browser State) */}
        <div className="col-span-12 lg:col-span-8 flex flex-col min-h-0">
          <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }} className="glass-panel rounded-xl flex flex-col flex-1 min-h-0 relative overflow-hidden group">

            {/* Overlay Scanner Effect */}
            {status === "Running" && (
              <div className="absolute top-0 left-0 w-full h-[2px] bg-cyan-400 shadow-[0_0_15px_#06b6d4] z-20 animate-[scan_3s_ease-in-out_infinite]"></div>
            )}

            <div className="absolute top-4 left-4 z-20 bg-black/60 backdrop-blur border border-white/10 px-3 py-1.5 rounded-full flex items-center gap-2">
              <Eye className="w-4 h-4 text-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-bold text-gray-200">Optic Sensor</span>
            </div>

            <div className="flex-1 bg-black/80 flex items-center justify-center p-8 overflow-hidden">
              <AnimatePresence mode="wait">
                {domImage ? (
                  <motion.img
                    key={domImage.substring(0, 20)}
                    initial={{ opacity: 0, scale: 1.05 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    src={`data:image/jpeg;base64,${domImage}`}
                    className="max-w-full max-h-full object-contain rounded border border-white/10 shadow-2xl"
                    alt="Agent View"
                  />
                ) : (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center gap-4 border border-dashed border-cyan-900/50 rounded-xl p-12">
                    <Globe className={`w-16 h-16 ${status === "Running" ? "text-cyan-500 animate-pulse" : "text-gray-700"}`} />
                    <p className={`font-mono text-sm ${status === "Running" ? "text-cyan-400 animate-pulse" : "text-gray-500"}`}>
                      {status === "Running" ? "ESTABLISHING SIGNAL..." : "NO SIGNAL"}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>

      </div>

      <style dangerouslySetInnerHTML={{
        __html: `
        @keyframes scan {
          0% { top: 0%; opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
      `}} />
    </div>
  );
}
