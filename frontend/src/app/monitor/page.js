'use client';

import { useState, useRef, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

const APP_NAME = 'daedalus';

function MonitorContent() {
  const searchParams = useSearchParams();
  const [prompt, setPrompt] = useState('');
  const [events, setEvents] = useState([]);
  const [triggeredAgents, setTriggeredAgents] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const eventsEndRef = useRef(null);
  const userIdRef = useRef(null);
  const hasAutoRun = useRef(false);

  const scrollToBottom = () => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [events]);

  useEffect(() => {
    // Initialize User ID
    let uid = localStorage.getItem('user_id');
    if (!uid) {
      uid = `user_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('user_id', uid);
    }
    userIdRef.current = uid;

    // Check for autoRun - only trigger once when params are available
    const autoRun = searchParams.get('autoRun');
    const paramPrompt = searchParams.get('prompt');

    if (autoRun === 'true' && paramPrompt && !hasAutoRun.current) {
      hasAutoRun.current = true;
      setPrompt(paramPrompt);
      runAgent(paramPrompt);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const initSession = async () => {
    if (sessionId) return sessionId;

    try {
      const res = await fetch(`/apps/${APP_NAME}/users/${userIdRef.current}/sessions`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        console.log('Session created:', data.id);
        setSessionId(data.id);
        return data.id;
      } else {
        console.error('Failed to create session');
        return null;
      }
    } catch (e) {
      console.error('Error connecting to backend:', e);
      return null;
    }
  };

  async function runAgent(inputPrompt) {
    if (!inputPrompt?.trim()) return;

    setIsStreaming(true);
    setEvents([]);
    setTriggeredAgents([]);

    const sid = await initSession();
    if (!sid) {
      alert("Failed to initialize session. check console.");
      setIsStreaming(false);
      return;
    }

    try {
      const response = await fetch('/run_sse', {
        method: 'POST',
        body: JSON.stringify({
          appName: APP_NAME,
          userId: userIdRef.current,
          sessionId: sid,
          newMessage: {
            parts: [{ text: inputPrompt }],
            role: 'user',
          },
          streaming: true,
        }),
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.body) {
        throw new Error('ReadableStream not supported in this browser.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const processLine = (line) => {
        if (line.startsWith('data: ')) {
          const dataContent = line.replace('data: ', '').trim();
          if (dataContent === '[DONE]') {
            setIsStreaming(false);
            return;
          }
          if (!dataContent) return;

          try {
            const rawJson = JSON.parse(dataContent);
            if (rawJson.author) {
              const usage = rawJson.usageMetadata || {};
              let title = rawJson.title || 'Untitled Event';

              if (rawJson.author === 'system' && rawJson.content?.parts?.[0]?.text) {
                title = rawJson.content.parts[0].text.substring(0, 100) + '...';
              }

              const filteredEvent = {
                id: rawJson.id || Math.random().toString(36).substr(2, 9),
                modelVersion: rawJson.modelVersion || 'unknown',
                usage: {
                  prompt: usage.promptTokenCount || 0,
                  candidate: usage.candidatesTokenCount || 0,
                  thoughts: usage.thoughtsTokenCount || 0
                },
                author: rawJson.author || 'unknown',
                title: title
              };

              setEvents(prev => {
                if (prev.some(e => e.id === filteredEvent.id)) return prev;
                return [...prev, filteredEvent];
              });

              setTriggeredAgents(prev => {
                if (prev.length === 0 || prev[prev.length - 1] !== rawJson.author) {
                  return [...prev, rawJson.author];
                }
                return prev;
              });
            }

          } catch (err) {
            console.log('Non-JSON data or parse error:', dataContent);
          }
        }
      };

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        const lines = buffer.split('\n');

        // Keep the last partial line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          processLine(line);
        }
      }

      // Process any remaining buffer
      if (buffer.trim()) {
        processLine(buffer);
      }
    } catch (error) {
      console.error('Error streaming:', error);
      setIsStreaming(false);
    }
  }

  async function startAgentRun(e) {
    e.preventDefault();
    runAgent(prompt);
  }

  if (!isStreaming && events.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-white p-4">
        <div className="w-full max-w-md bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-2xl shadow-2xl animate-in zoom-in duration-500">
          <h1 className="text-3xl font-bold mb-6 text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-300 to-purple-300">Iris Agent Monitor</h1>
          <form onSubmit={startAgentRun} className="flex flex-col gap-4">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your prompt..."
              className="p-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500 focus:bg-white/10 transition-colors"
            />
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded-lg transition-all shadow-lg hover:shadow-blue-500/30"
            >
              Run Agent
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full text-white overflow-hidden">
      <div className="w-1/2 border-r border-white/10 p-6 overflow-y-auto flex flex-col bg-black/20 backdrop-blur-md">
        <div className="mb-4 flex justify-between items-center sticky top-0 z-10 bg-black/40 backdrop-blur-xl p-2 rounded-lg border border-white/5">
          <h2 className="text-xl font-bold text-gray-100">Live Event Stream</h2>
          <button
            onClick={() => { setIsStreaming(false); setEvents([]); setTriggeredAgents([]); setPrompt(''); }}
            className="text-xs px-3 py-1 rounded bg-white/5 hover:bg-white/10 border border-white/10 transition-colors"
          >
            New Run
          </button>
        </div>

        <div className="space-y-4 flex-grow">
          {events.map((event) => (
            <div key={event.id} className="bg-white/5 border border-white/10 rounded-xl p-4 shadow-lg backdrop-blur-sm hover:bg-white/10 transition-all duration-300 animate-in fade-in slide-in-from-bottom-4">
              <div className="flex justify-between items-start mb-2">
                <span className={`px-2 py-1 rounded-md text-xs font-semibold uppercase tracking-wide shadow-sm ${getAuthorColor(event.author)}`}>
                  {event.author}
                </span>
                <span className="text-xs text-gray-400 font-mono bg-black/20 px-2 py-0.5 rounded">{event.modelVersion}</span>
              </div>

              <h3 className="text-lg font-medium text-gray-100 mb-3 leading-snug">{event.title}</h3>

              <div className="flex gap-4 text-xs text-gray-400 border-t border-white/5 pt-3 font-mono">
                <div className="flex flex-col">
                  <span className="text-[10px] uppercase text-gray-500">Prompt</span>
                  <span className="text-gray-300">{event.usage.prompt}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] uppercase text-gray-500">Candidate</span>
                  <span className="text-gray-300">{event.usage.candidate}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] uppercase text-gray-500">Thoughts</span>
                  <span className="text-gray-300">{event.usage.thoughts}</span>
                </div>
              </div>
            </div>
          ))}
          <div ref={eventsEndRef} />
        </div>
      </div>

      <div className="w-1/2 p-6 overflow-y-auto border-l border-white/10 bg-black/20 backdrop-blur-md">
        <h2 className="text-xl font-bold mb-6 text-gray-200 sticky top-0 bg-black/40 backdrop-blur-xl p-2 rounded-lg border border-white/5 z-10">Agents Triggered</h2>
        <div className="space-y-0 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-blue-500/50 before:to-transparent pl-2">
          {triggeredAgents.map((agent, index) => (
            <div key={index} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active mb-8 last:mb-0">
              <div className="flex items-center justify-center w-10 h-10 rounded-full border-2 border-white/20 bg-gray-900 group-[.is-active]:bg-blue-600/20 text-gray-500 group-[.is-active]:text-blue-200 shadow-[0_0_15px_rgba(59,130,246,0.3)] shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 ml-1 backdrop-blur-md z-10">
                <span className="text-sm font-bold">{index + 1}</span>
              </div>
              <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-white/10 bg-white/5 shadow-lg ml-4 hover:bg-white/10 transition-colors backdrop-blur-sm">
                <div className="font-bold text-gray-200 tracking-wide">{agent}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function getAuthorColor(author) {
  const colors = {
    'prompt_generator': 'bg-blue-500/20 text-blue-200 border border-blue-500/30',
    'image_generator': 'bg-purple-500/20 text-purple-200 border border-purple-500/30',
    'publisher': 'bg-green-500/20 text-green-200 border border-green-500/30',
    'iris_agent': 'bg-indigo-500/20 text-indigo-200 border border-indigo-500/30',
    'system': 'bg-red-500/20 text-red-200 border border-red-500/30',
    'unknown': 'bg-gray-500/20 text-gray-300 border border-gray-500/30'
  };
  return colors[author] || colors['unknown'];
}

export default function MonitorPage() {
  return (
    <Suspense fallback={<div className="text-white text-center mt-10">Loading Monitor...</div>}>
      <MonitorContent />
    </Suspense>
  );
}
