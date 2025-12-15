
import React, { useState, useRef, useEffect } from 'react';
import { Send, Zap, Activity } from 'lucide-react';
import AgentNode from './components/AgentNode';
import DebateStream from './components/DebateStream';
import VerdictReveal from './components/VerdictReveal';
import ConfigPanel from './components/ConfigPanel';

const API_URL = 'ws://localhost:8000/ws/verify';

function App() {
  const [ws, setWs] = useState(null);
  const [input, setInput] = useState('');
  const [inputType, setInputType] = useState('Text'); // Text or URL
  const [isProcessing, setIsProcessing] = useState(false);

  // Configuration Parameters
  const [maxIterations, setMaxIterations] = useState(3);
  const [maxSearches, setMaxSearches] = useState(-1);
  const [language, setLanguage] = useState('Italian');
  const [proPersonality, setProPersonality] = useState('ASSERTIVE');
  const [contraPersonality, setContraPersonality] = useState('ASSERTIVE');

  // Debate State
  const [messages, setMessages] = useState([]);
  const [statusText, setStatusText] = useState('SYSTEM READY');
  const [proStatus, setProStatus] = useState('idle');
  const [contraStatus, setContraStatus] = useState('idle');
  const [verdict, setVerdict] = useState(null);

  const [isVerdictVisible, setIsVerdictVisible] = useState(true);

  useEffect(() => {
    return () => {
      if (ws) ws.close();
    };
  }, [ws]);

  const startVerification = () => {
    if (!input.trim()) return;

    setIsProcessing(true);
    setMessages([]);
    setVerdict(null);
    setIsVerdictVisible(true);
    setStatusText('INITIALIZING UPLINK...');

    // Connect to WebSocket
    const socket = new WebSocket(API_URL);

    socket.onopen = () => {
      console.log('Connected');
      setStatusText('CONNECTED');
      socket.send(JSON.stringify({
        input,
        type: inputType,
        max_iterations: maxIterations,
        max_searches: maxSearches,
        language: language,
        proPersonality: proPersonality,
        contraPersonality: contraPersonality
      }));
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleUpdate(data);
    };

    socket.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setStatusText('CONNECTION ERROR');
      setIsProcessing(false);
    };

    socket.onclose = () => {
      console.log('Disconnected');
      if (!verdict) setIsProcessing(false);
    };

    setWs(socket);
  };

  const handleUpdate = (payload) => {
    const { type, node, data, description } = payload;

    if (description) setStatusText(description.toUpperCase());

    // Agent Animations - Predictive State
    // We set status for the NEXT node based on the one that just completed
    if (node === 'initialize') {
      setStatusText('EXTRACTING CLAIM...');
    } else if (node === 'extract') {
      // Next: PRO Research
      setProStatus('thinking');
      setContraStatus('idle');
    } else if (node === 'pro_research') {
      // Next: CONTRA Research
      setProStatus('idle');
      setContraStatus('thinking');
    } else if (node === 'contra_research') {
      // Next: PRO Debate Turn (Round 1)
      setProStatus('thinking');
      setContraStatus('idle');
    } else if (node === 'pro_node') {
      // Next: CONTRA Debate Turn
      setProStatus('idle');
      setContraStatus('thinking');
    } else if (node === 'contra_node') {
      // Next: PRO Debate Turn (Round X) or Judge
      // We assume debate continues for UI feedback
      setProStatus('thinking');
      setContraStatus('idle');
    } else if (node === 'debate') {
      // Fallback or legacy
      if (data && data.messages) {
        const lastMsg = data.messages[data.messages.length - 1];
        if (lastMsg.agent === 'PRO') {
          setProStatus('speaking');
          setContraStatus('idle');
        } else {
          setProStatus('idle');
          setContraStatus('speaking');
        }
      }
    } else {
      setProStatus('idle');
      setContraStatus('idle');
    }

    // New Messages
    if (type === 'update' && data.messages) {
      // Just replace the whole list or append new ones? 
      // LangGraph returns full history usually, or diffs. 
      // Our backend implementation sends the node state. 
      // If node state has 'messages', it's the full list.
      // We map them to our format.
      const msgs = data.messages.map(m => ({
        agent: m.agent || m.type, // Fallback
        content: m.content,
        // Backend sends round_count. If it's 0 (research), keep 0. If >0, use it.
        round: data.round_count !== undefined ? data.round_count : 1,
        sources: m.sources
      }));

      // Append new messages to existing history
      // We use functional update to ensure we have the latest state
      setMessages(prev => {
        // Simple deduplication based on content and agent to avoid react strict mode double-invokes
        const newUnique = msgs.filter(newMsg =>
          !prev.some(existing =>
            existing.content === newMsg.content &&
            existing.agent === newMsg.agent &&
            existing.round === newMsg.round
          )
        );
        return [...prev, ...newUnique];
      });
    }

    // Verdict
    if (type === 'verdict') {
      setVerdict(data); // data is the Verdict object
      setIsProcessing(false);
      setIsVerdictVisible(true);
      ws.close();
    }

    // Completion
    if (type === 'complete') {
      setIsProcessing(false);
      if (ws) ws.close();
    }

    if (type === 'error') {
      setStatusText(`ERROR: ${payload.message}`);
      setIsProcessing(false);
    }
  };

  const reset = () => {
    setVerdict(null);
    setMessages([]);
    setInput('');
    setIsProcessing(false);
    setStatusText('SYSTEM READY');
    setProStatus('idle');
    setContraStatus('idle');
    setIsVerdictVisible(true);
  };

  return (
    <div className="flex flex-col h-screen max-h-screen bg-[url('/bg-grid.png')] bg-cover">
      {/* Header */}
      <header className="p-4 border-b border-white/10 flex justify-between items-center bg-black/20 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <Activity className="text-accent" />
          <h1 className="text-xl font-bold tracking-[0.2em] glow-text">VERITAS<span className="text-accent">LOOP</span></h1>
        </div>
        <div className="font-mono text-xs text-muted">
          STATUS: <span className={isProcessing ? 'text-green-400 animate-pulse' : 'text-gray-500'}>{statusText}</span>
        </div>
      </header>

      {/* Main Grid */}
      <main className="flex-1 grid grid-cols-1 md:grid-cols-[1fr_2fr_1fr] overflow-hidden min-h-0">

        {/* Left: PRO Agent */}
        <section className="p-8 border-r border-white/5 flex flex-col justify-center relative">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-900/10 to-transparent pointer-events-none" />
          <AgentNode role="PRO" label="PRO AGENT" status={proStatus} personality={proPersonality} />
        </section>

        {/* Center: Arena */}
        <section className="flex flex-col relative bg-black/20 min-h-0 overflow-hidden relative">
          {/* Messages Area */}
          <DebateStream messages={messages} />

          {/* Show Verdict Button (Floating) */}
          {verdict && !isVerdictVisible && (
            <button
              onClick={() => setIsVerdictVisible(true)}
              className="absolute top-4 right-4 z-40 bg-accent text-white px-4 py-2 rounded-full font-bold shadow-lg hover:scale-105 transition-transform"
            >
              SHOW VERDICT
            </button>
          )}

          {/* Input Area (Only visible when not processing) */}
          <div className="p-6 border-t border-white/10 bg-black/40 backdrop-blur-md">

            <ConfigPanel
              maxIterations={maxIterations}
              setMaxIterations={setMaxIterations}
              maxSearches={maxSearches}
              setMaxSearches={setMaxSearches}
              inputType={inputType}
              setInputType={setInputType}
              language={language}
              setLanguage={setLanguage}
              proPersonality={proPersonality}
              setProPersonality={setProPersonality}
              contraPersonality={contraPersonality}
              setContraPersonality={setContraPersonality}
              isProcessing={isProcessing}
            />

            {/* Main Input */}
            <div className="flex gap-4 max-w-3xl mx-auto">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && startVerification()}
                placeholder={inputType === 'URL' ? "Paste article URL..." : "Enter claim to verify..."}
                className="flex-1 bg-white/5 border border-white/10 rounded px-4 py-3 focus:outline-none focus:border-accent focus:bg-white/10 transition-colors text-lg shadow-inner"
                disabled={isProcessing}
              />

              <button
                onClick={startVerification}
                disabled={isProcessing || !input}
                className="bg-accent hover:bg-opacity-80 text-white px-8 py-3 rounded font-bold flex items-center gap-2 transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(var(--accent-rgb),0.3)]"
              >
                <Send size={20} />
                VERIFY
              </button>
            </div>
          </div>
        </section>

        {/* Right: CONTRA Agent */}
        <section className="p-8 border-l border-white/5 flex flex-col justify-center relative">
          <div className="absolute inset-0 bg-gradient-to-l from-orange-900/10 to-transparent pointer-events-none" />
          <AgentNode role="CONTRA" label="CONTRA AGENT" status={contraStatus} personality={contraPersonality} />
        </section>

      </main>

      {/* Verdict Overlay */}
      {isVerdictVisible && (
        <VerdictReveal
          data={verdict}
          onReset={reset}
          onReviewDebate={() => setIsVerdictVisible(false)}
        />
      )}
    </div>
  );
}

export default App;
