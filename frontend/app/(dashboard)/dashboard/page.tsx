"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { 
  Database, 
  Plus, 
  Search, 
  MoreVertical, 
  ExternalLink, 
  MessageSquare, 
  RefreshCcw,
  AlertCircle,
  Clock,
  Settings
} from "lucide-react";
import { api } from "@/lib/api";
import { authStore } from "@/lib/auth-store";

export default function DashboardPage() {
  const [databases, setDatabases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDatabases = async () => {
    const session = authStore.getSession();
    if (!session) return;
    
    try {
      setLoading(true);
      const data = (await api.getDatabases({ token: session.token })) as any;
      setDatabases(data.items || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatabases();
  }, []);

  return (
    <div className="space-y-8 pb-20">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Intelligence Dashboard</h1>
          <p className="text-muted-foreground mt-2">Manage your data connections and query insights.</p>
        </div>
        <Link 
          href="/databases/new"
          className="bg-primary hover:bg-primary/90 text-white px-5 py-2.5 rounded-xl font-semibold flex items-center gap-2 transition-all shadow-lg shadow-primary/20"
        >
          <Plus size={20} />
          New Connection
        </Link>
      </div>

      {/* Stats/Quick Actions Placeholder */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: "Active Connections", value: databases.length, color: "text-primary" },
          { label: "Total Queries", value: "0", color: "text-accent" },
          { label: "MDL Health", value: "98%", color: "text-emerald-500" },
        ].map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass p-6 rounded-2xl border border-border/50"
          >
            <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
            <p className={`text-3xl font-bold mt-2 ${stat.color}`}>{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Database List */}
      <div className="glass rounded-2xl overflow-hidden border border-border/50">
        <div className="p-6 border-b border-border/50 flex items-center justify-between bg-muted/20">
          <div className="flex items-center gap-2">
            <Database className="text-primary w-5 h-5" />
            <h2 className="font-semibold text-lg">Your Databases</h2>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input 
              type="text" 
              placeholder="Search datasets..." 
              className="bg-muted/50 border border-border rounded-lg py-1.5 pl-9 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-primary/50 text-foreground"
            />
          </div>
        </div>

        <div className="divide-y divide-border/50">
          {loading ? (
            <div className="p-20 flex flex-col items-center justify-center gap-4">
              <RefreshCcw className="w-8 h-8 text-primary animate-spin" />
              <p className="text-muted-foreground text-sm">Synchronizing connections...</p>
            </div>
          ) : databases.length === 0 ? (
            <div className="p-20 flex flex-col items-center justify-center text-center gap-4">
              <div className="bg-muted p-4 rounded-full">
                <Database className="w-8 h-8 text-muted-foreground" />
              </div>
              <div>
                <h3 className="font-semibold">No databases connected</h3>
                <p className="text-muted-foreground text-sm max-w-xs mt-1">Get started by adding your first PostgreSQL connection.</p>
              </div>
              <Link href="/databases/new" className="text-primary font-medium hover:underline text-sm flex items-center gap-1 mt-2">
                Learn how to connect <ExternalLink size={12} />
              </Link>
            </div>
          ) : (
            databases.map((db, i) => (
              <motion.div
                key={db.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.05 }}
                className="p-6 hover:bg-muted/30 transition-colors flex items-center justify-between group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center ring-1 ring-primary/20 group-hover:scale-110 transition-transform">
                    <Database className="text-primary w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold flex items-center gap-2">
                      {db.name}
                      <span className="bg-emerald-500/10 text-emerald-500 text-[10px] px-2 py-0.5 rounded-full ring-1 ring-emerald-500/20">
                        Active
                      </span>
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1 font-mono">
                      {db.username}@{db.host}:{db.port}/{db.db_name}
                    </p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                        <Clock size={10} /> Created {new Date(db.created_at).toLocaleDateString()}
                      </span>
                      <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                        <RefreshCcw size={10} /> MDL v1.0
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Link
                    href={`/chat/${db.id}`}
                    className="p-2 px-4 rounded-lg bg-background border border-border hover:bg-primary/10 hover:border-primary/50 text-foreground hover:text-primary transition-all flex items-center gap-2 text-sm font-medium"
                  >
                    <MessageSquare size={16} />
                    Query
                  </Link>
                  <Link
                    href={`/databases/${db.id}`}
                    className="p-2 rounded-lg bg-background border border-border hover:bg-muted transition-all text-muted-foreground"
                  >
                    <Settings size={18} />
                  </Link>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>
      
      {/* Help Banner */}
      <div className="p-6 glass rounded-2xl bg-primary/5 border border-primary/20 flex items-start gap-4">
        <AlertCircle className="text-primary w-6 h-6 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-bold text-sm">Pro Tip: Restricted Access</h4>
          <p className="text-xs text-muted-foreground mt-1 max-w-2xl">
            Ensure your database user has **read-only** permissions. The agent can block tables like `users` or `passwords` automatically if added to the Blocked Tables list in settings.
          </p>
        </div>
      </div>
    </div>
  );
}
