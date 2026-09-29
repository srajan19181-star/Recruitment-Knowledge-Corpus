"use client";

import { useState, useEffect, useRef } from "react";
import {
  Send,
  Plus,
  Trash2,
  ThumbsUp,
  ThumbsDown,
  Square,
  ShieldCheck,
  Sparkles,
  Zap,
  Clock,
  FileText,
  Loader2,
} from "lucide-react";
import { CitationPanel, CitationData } from "@/components/CitationPanel";
import { ComplianceModal } from "@/components/ComplianceModal";
import { DraftAdModal } from "@/components/DraftAdModal";

interface Message {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: CitationData[];
  cache_hit?: boolean;
  latency_ms?: number;
  feedback_value?: number;
}

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
}

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [activeCitation, setActiveCitation] = useState<CitationData | null>(null);
  const [complianceOpen, setComplianceOpen] = useState(false);
  const [draftOpen, setDraftOpen] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Fetch conversations on mount
  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const res = await fetch("/api/conversations");
      if (!res.ok) return;
      const data = await res.json();
      setConversations(data.conversations || []);
      if (data.conversations?.length > 0 && !activeConvId) {
        loadConversation(data.conversations[0].id);
      }
    } catch {
      // Ignore initial fetch errors
    }
  };

  const loadConversation = async (id: string) => {
    setActiveConvId(id);
    setActiveCitation(null);
    try {
      const res = await fetch(`/api/conversations/${id}`);
      if (!res.ok) return;
      const data = await res.json();
      setMessages(data.messages || []);
    } catch {
      // Ignore
    }
  };

  const createNewChat = async () => {
    try {
      const res = await fetch("/api/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Conversation" }),
      });
      if (!res.ok) return;
      const data = await res.json();
      setConversations((prev) => [data.conversation, ...prev]);
      setActiveConvId(data.conversation.id);
      setMessages([]);
      setActiveCitation(null);
    } catch {
      // Ignore
    }
  };

  const deleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`/api/conversations/${id}`, { method: "DELETE" });
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConvId === id) {
        const remaining = conversations.filter((c) => c.id !== id);
        if (remaining.length > 0) {
          loadConversation(remaining[0].id);
        } else {
          setActiveConvId(null);
          setMessages([]);
        }
      }
    } catch {
      // Ignore
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || streaming) return;

    let convId = activeConvId;
    if (!convId) {
      const res = await fetch("/api/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Conversation" }),
      });
      const data = await res.json();
      convId = data.conversation.id;
      setActiveConvId(convId);
      setConversations((prev) => [data.conversation, ...prev]);
    }

    const userMessageContent = input.trim();
    setInput("");

    // Optimistically append user message
    const tempUserMsg: Message = { role: "user", content: userMessageContent };
    const tempAssistantMsg: Message = { role: "assistant", content: "" };
    setMessages((prev) => [...prev, tempUserMsg, tempAssistantMsg]);
    setStreaming(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const res = await fetch(`/api/conversations/${convId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: userMessageContent }),
        signal: abortController.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error("Failed to connect to streaming endpoint");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let accumulatedContent = "";
      let finalCitations: CitationData[] = [];
      let finalCacheHit = false;
      let finalLatency = 0;
      let finalMsgId = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("event:")) {
            currentEvent = trimmed.replace("event:", "").trim();
          } else if (trimmed.startsWith("data:")) {
            const dataStr = trimmed.replace("data:", "").trim();
            if (currentEvent === "token") {
              accumulatedContent += dataStr;
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last && last.role === "assistant") {
                  last.content = accumulatedContent;
                }
                return updated;
              });
            } else if (currentEvent === "done") {
              try {
                const parsed = JSON.parse(dataStr);
                finalMsgId = parsed.message_id;
                finalCitations = parsed.citations || [];
                finalCacheHit = parsed.cache_hit || false;
                finalLatency = parsed.latency_ms || 0;
              } catch {
                // Ignore json parse error
              }
            }
          }
        }
      }

      // Update assistant message with completed state
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.role === "assistant") {
          last.id = finalMsgId;
          last.content = accumulatedContent;
          last.citations = finalCitations;
          last.cache_hit = finalCacheHit;
          last.latency_ms = finalLatency;
        }
        return updated;
      });

      fetchConversations();
    } catch (err: unknown) {
      if (abortController.signal.aborted) {
        // Stream aborted by user
      } else {
        const errText = err instanceof Error ? err.message : "Error streaming response";
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.role === "assistant") {
            last.content = `[Generation failed: ${errText}]`;
          }
          return updated;
        });
      }
    } finally {
      setStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setStreaming(false);
    }
  };

  const handleFeedback = async (messageId: string | undefined, value: 1 | -1) => {
    if (!messageId) return;
    try {
      await fetch(`/api/messages/${messageId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value }),
      });
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, feedback_value: value } : m))
      );
    } catch {
      // Ignore
    }
  };

  // Helper to parse [doc_id, p. X] citations in assistant text and make them clickable
  const renderMessageContent = (text: string, citations?: CitationData[]) => {
    const citationRegex = /\[([a-zA-Z0-9_\-\s]+?)(?:,\s*p\.\s*(\d+))?\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }

      const docName = match[1].trim();
      const pageNum = match[2] ? parseInt(match[2], 10) : undefined;
      const matchedCitation = citations?.find(
        (c) => c.doc_id === docName || c.doc_id.includes(docName)
      ) || {
        chunk_id: "retrieved-chunk",
        doc_id: docName,
        page: pageNum,
      };

      parts.push(
        <button
          key={match.index}
          onClick={() => setActiveCitation(matchedCitation)}
          className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
        >
          <FileText className="w-3 h-3 mr-1 inline" />
          <span>{docName}{pageNum ? `, p. ${pageNum}` : ""}</span>
        </button>
      );
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return <span className="whitespace-pre-wrap">{parts}</span>;
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-200 bg-white flex flex-col">
        <div className="p-3 border-b border-slate-100 flex items-center justify-between">
          <button
            onClick={createNewChat}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-3 rounded-lg text-xs transition-colors flex items-center justify-center space-x-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.length === 0 && (
            <div className="text-center py-8 text-xs text-slate-400">No conversations yet</div>
          )}
          {conversations.map((conv) => {
            const isActive = conv.id === activeConvId;
            return (
              <div
                key={conv.id}
                onClick={() => loadConversation(conv.id)}
                className={`p-2.5 rounded-lg text-xs cursor-pointer flex items-center justify-between group transition-colors ${
                  isActive ? "bg-slate-100 text-slate-900 font-medium" : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <span className="truncate flex-1 pr-2">{conv.title}</span>
                <button
                  onClick={(e) => deleteConversation(conv.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-600 rounded"
                  title="Delete chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
        </div>

        {/* Quick Tools in Sidebar Footer */}
        <div className="p-3 border-t border-slate-100 bg-slate-50 space-y-1.5">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
            Recruiter Quick Actions
          </p>
          <button
            onClick={() => setComplianceOpen(true)}
            className="w-full text-left px-2.5 py-1.5 rounded text-xs text-slate-700 hover:bg-white hover:shadow-xs flex items-center space-x-2 border border-slate-200 bg-white"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
            <span>Audit Job Ad Compliance</span>
          </button>
          <button
            onClick={() => setDraftOpen(true)}
            className="w-full text-left px-2.5 py-1.5 rounded text-xs text-slate-700 hover:bg-white hover:shadow-xs flex items-center space-x-2 border border-slate-200 bg-white"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Draft Compliant Job Ad</span>
          </button>
        </div>
      </aside>

      {/* Main Chat Interface */}
      <section className="flex-1 flex flex-col bg-slate-50 overflow-hidden">
        {/* Messages scroll area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 max-w-4xl w-full mx-auto">
          {messages.length === 0 && (
            <div className="py-16 text-center max-w-lg mx-auto space-y-3">
              <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center mx-auto">
                <FileText className="w-6 h-6" />
              </div>
              <h2 className="text-base font-bold text-slate-800">Recruiter Knowledge & Compliance Copilot</h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                Ask questions regarding statutory salary transparency laws (NYC, Colorado, California, Washington),
                recruitment marketing unit economics (CPC, CPA), application funnels, or inclusive job ad copywriting.
              </p>
              <div className="pt-2 flex flex-wrap justify-center gap-2">
                {[
                  "What are the mandatory pay range rules in New York City?",
                  "How does Colorado EPEW Act govern remote job benefits?",
                  "What masculine-coded words should be avoided in job descriptions?",
                  "Explain the formula for Cost-Per-Application (CPA) and budget pacing.",
                ].map((sampleQuery, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInput(sampleQuery);
                    }}
                    className="text-xs bg-white border border-slate-200 hover:border-blue-400 p-2 rounded-lg text-slate-700 text-left transition-colors"
                  >
                    "{sampleQuery}"
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, index) => {
            const isUser = msg.role === "user";
            return (
              <div key={index} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-2xl rounded-xl p-4 text-sm shadow-xs ${
                    isUser
                      ? "bg-blue-600 text-white rounded-br-xs"
                      : "bg-white border border-slate-200 text-slate-800 rounded-bl-xs space-y-2.5"
                  }`}
                >
                  <div className="leading-relaxed">
                    {isUser ? msg.content : renderMessageContent(msg.content, msg.citations)}
                  </div>

                  {!isUser && (
                    <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                      <div className="flex items-center space-x-3">
                        {msg.cache_hit && (
                          <span className="inline-flex items-center text-emerald-600 font-medium">
                            <Zap className="w-3 h-3 mr-0.5" />
                            <span>Served from Semantic Cache</span>
                          </span>
                        )}
                        {msg.latency_ms !== undefined && msg.latency_ms > 0 && (
                          <span className="inline-flex items-center text-slate-400">
                            <Clock className="w-3 h-3 mr-0.5" />
                            <span>{msg.latency_ms}ms</span>
                          </span>
                        )}
                      </div>

                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => handleFeedback(msg.id, 1)}
                          className={`p-1 rounded hover:bg-slate-100 ${
                            msg.feedback_value === 1 ? "text-blue-600 font-bold" : "text-slate-400"
                          }`}
                          title="Thumbs up"
                        >
                          <ThumbsUp className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => handleFeedback(msg.id, -1)}
                          className={`p-1 rounded hover:bg-slate-100 ${
                            msg.feedback_value === -1 ? "text-red-600 font-bold" : "text-slate-400"
                          }`}
                          title="Thumbs down"
                        >
                          <ThumbsDown className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-white border-t border-slate-200 max-w-4xl w-full mx-auto">
          <form onSubmit={handleSend} className="relative">
            <textarea
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(e);
                }
              }}
              placeholder="Ask about recruitment compliance or search your document corpus... (Enter to send, Shift+Enter for newline)"
              className="w-full pl-3 pr-24 py-2.5 border border-slate-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="absolute right-2.5 bottom-3.5 flex items-center space-x-1.5">
              {streaming ? (
                <button
                  type="button"
                  onClick={handleStop}
                  className="bg-red-500 hover:bg-red-600 text-white px-2.5 py-1 rounded-md text-xs font-medium flex items-center space-x-1"
                >
                  <Square className="w-3 h-3 fill-current" />
                  <span>Stop</span>
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white p-1.5 rounded-md transition-colors"
                >
                  <Send className="w-4 h-4" />
                </button>
              )}
            </div>
          </form>
        </div>
      </section>

      {/* Right Drawer Citation Panel */}
      <CitationPanel citation={activeCitation} onClose={() => setActiveCitation(null)} />

      {/* Tool Modals */}
      <ComplianceModal isOpen={complianceOpen} onClose={() => setComplianceOpen(false)} />
      <DraftAdModal
        isOpen={draftOpen}
        onClose={() => setDraftOpen(false)}
        onInsertToChat={(text) => setInput(text)}
      />
    </div>
  );
}
