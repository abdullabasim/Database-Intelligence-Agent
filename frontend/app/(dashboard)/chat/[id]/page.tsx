"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  Database, 
  Code, 
  Table as TableIcon,
  ChevronDown,
  ChevronUp,
  RefreshCcw,
  Sparkles,
  Terminal,
  MessageSquare
} from "lucide-react";
import { api } from "@/lib/api";
import { authStore } from "@/lib/auth-store";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sql?: string;
  data?: any[];
  steps?: string[];
  columns?: string[];
}

export default function ChatPage() {
  const { id } = useParams();
  const [db, setDb] = useState<any>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mdlStatus, setMdlStatus] = useState<"loading" | "ready" | "missing">("loading");
  const scrollRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      const session = authStore.getSession();
      if (!session) return;
      try {
        const database = await api.request<any>(`/databases/${id}`, { auth: { token: session.token } });
        setDb(database);
        
        try {
          await api.getLatestMDL(id as string, { token: session.token });
          setMdlStatus("ready");
        } catch {
          setMdlStatus("missing");
        }
      } catch (err) {
        console.error(err);
        router.push("/dashboard");
      }
    };
    fetchData();
  }, [id, router]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    const session = authStore.getSession();
    if (!session) return;

    const assistantId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      steps: [],
    };

    setMessages((prev) => [...prev, assistantMessage]);

    try {
      await api.streamAskQuestion(
        { question: input, database_id: id as string },
        { token: session.token },
        (event, data) => {
          setMessages((prev) => prev.map((msg) => {
            if (msg.id === assistantId) {
              if (event === "step") {
                return { ...msg, steps: [...(msg.steps || []), data] };
              }
              if (event === "sql") {
                return { ...msg, sql: data };
              }
              if (event === "result") {
                return { ...msg, data: data.rows, columns: data.columns };
              }
              if (event === "answer") {
                return { ...msg, content: data };
              }
              if (event === "error") {
                return { ...msg, content: `Error: ${data}` };
              }
            }
            return msg;
          }));
        }
      );
    } catch (err: any) {
      setMessages((prev) => prev.map((msg) => 
        msg.id === assistantId 
          ? { ...msg, content: `Error: ${err.message}. Please ensure the MDL is refreshed.` }
          : msg
      ));
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshMDL = async () => {
    const session = authStore.getSession();
    if (!session) return;
    try {
      setMdlStatus("loading");
      await api.refreshMDL({ database_id: id as string, name: "latest" }, { token: session.token });
      alert("MDL Refresh started in background. Please wait a moment.");
      setMdlStatus("ready");
    } catch (err) {
      alert("Failed to start refresh");
      setMdlStatus("missing");
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-5xl mx-auto">
      {/* Chat Header */}
      <div className="glass p-4 px-6 rounded-2xl border border-border/50 flex items-center justify-between mb-4 shadow-lg shadow-primary/5">
        <div className="flex items-center gap-3">
          <div className="bg-primary/10 p-2 rounded-lg ring-1 ring-primary/20">
            <Database className="text-primary w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-sm leading-none">{db?.name || "Loading..."}</h2>
            <p className="text-[10px] text-muted-foreground mt-1 font-mono uppercase tracking-wider">
              {db?.db_name} • {mdlStatus === "ready" ? "MDL Indexed" : "MDL Required"}
            </p>
          </div>
        </div>
        
        {mdlStatus === "missing" && (
          <button 
            onClick={handleRefreshMDL}
            className="text-xs bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 px-3 py-1.5 rounded-lg font-medium flex items-center gap-2 transition-all ring-1 ring-amber-500/30"
          >
            <RefreshCcw size={12} />
            Initialize Context
          </button>
        )}
      </div>

      {/* Messages */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-6 px-4 py-4 scrollbar-hide"
      >
        <AnimatePresence>
          {messages.length === 0 && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="h-full flex flex-col items-center justify-center text-center opacity-40 select-none"
            >
              <div className="p-6 bg-muted/30 rounded-full mb-4">
                <MessageSquare className="w-12 h-12 text-muted-foreground" />
              </div>
              <h3 className="font-bold text-lg">Knowledge Ready</h3>
              <p className="text-sm max-w-xs mt-2 text-muted-foreground">
                Ask anything about your data in natural language. The agent will translate it to SQL and analyze the results.
              </p>
            </motion.div>
          )}

          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "flex gap-4 w-full",
                message.role === "user" ? "flex-row-reverse" : "flex-row"
              )}
            >
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center shrink-0 shadow-sm",
                message.role === "user" ? "bg-accent/20 ring-1 ring-accent/30" : "bg-primary/20 ring-1 ring-primary/30"
              )}>
                {message.role === "user" ? <User size={16} className="text-accent" /> : <Bot size={16} className="text-primary" />}
              </div>

              <div className={cn(
                "max-w-[85%] space-y-3",
                message.role === "user" ? "text-right" : "text-left"
              )}>
                <div className={cn(
                  "inline-block p-4 rounded-2xl shadow-sm text-sm border",
                  message.role === "user" 
                    ? "bg-accent/5 border-accent/20 text-foreground rounded-tr-none" 
                    : "bg-muted/50 border-border/50 text-foreground rounded-tl-none font-medium leading-relaxed"
                )}>
                  {message.content}
                </div>

                {message.sql && (
                  <div className="mt-2 rounded-xl overflow-hidden border border-border/50 bg-[#0d1117]">
                    <div className="flex items-center justify-between px-4 py-2 bg-muted/20 border-b border-border/50">
                      <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                        <Terminal size={12} /> Generated SQL
                      </div>
                    </div>
                    <pre className="p-4 text-xs font-mono text-emerald-400 overflow-x-auto whitespace-pre-wrap">
                      <code>{message.sql}</code>
                    </pre>
                  </div>
                )}

                {message.data && message.data.length > 0 && (
                  <div className="mt-2 rounded-xl border border-border/50 bg-muted/10 overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-2 border-b border-border/50">
                      <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                        <TableIcon size={12} /> Execution Results
                      </div>
                      <span className="text-[10px] text-muted-foreground">{message.data.length} rows returned</span>
                    </div>
                    <div className="overflow-x-auto max-h-[300px]">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="bg-muted/20 border-b border-border/50">
                            {message.columns?.map((col) => (
                              <th key={col} className="p-2 px-3 font-bold text-muted-foreground uppercase tracking-wider">{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border/50">
                          {message.data.map((row, i) => (
                            <tr key={i} className="hover:bg-muted/20 transition-colors">
                              {message.columns?.map((col) => (
                                <td key={col} className="p-2 px-3 text-foreground/80 font-medium">
                                  {typeof row[col] === 'object' ? JSON.stringify(row[col]) : String(row[col])}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
          
          {loading && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-4"
            >
              <div className="w-8 h-8 rounded-lg bg-primary/20 ring-1 ring-primary/30 flex items-center justify-center shadow-sm">
                <Bot size={16} className="text-primary" />
              </div>
              <div className="bg-muted/50 border border-border/50 p-4 rounded-2xl rounded-tl-none flex items-center gap-3">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                <span className="text-xs text-muted-foreground font-medium italic">Agent is analyzing your database...</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input */}
      <form 
        onSubmit={handleSendMessage}
        className="mt-6 glass p-2 rounded-3xl border border-primary/20 shadow-2xl"
      >
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading || mdlStatus !== "ready"}
            className="flex-1 bg-transparent border-none focus:outline-none px-6 py-4 text-sm placeholder:text-muted-foreground"
            placeholder={mdlStatus === "ready" ? "Ask a question (e.g. 'Show me top 5 tables by row count')" : "Initialize Context to start chatting..."}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading || mdlStatus !== "ready"}
            className="bg-primary hover:bg-primary/90 text-white p-4 rounded-2xl transition-all shadow-lg shadow-primary/30 disabled:opacity-50 disabled:grayscale"
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  );
}
