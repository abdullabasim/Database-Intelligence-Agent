"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { 
  Database, 
  Plus, 
  Search, 
  ExternalLink, 
  MessageSquare, 
  RefreshCcw,
  Settings,
  Clock
} from "lucide-react";
import { api } from "@/lib/api";
import { authStore } from "@/lib/auth-store";

export default function DatabasesListPage() {
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
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Database Connections</h1>
          <p className="text-muted-foreground mt-1">Manage all your external data sources here.</p>
        </div>
        <Link 
          href="/databases/new"
          className="bg-primary hover:bg-primary/90 text-white px-5 py-2.5 rounded-xl font-semibold flex items-center gap-2 transition-all shadow-lg shadow-primary/20"
        >
          <Plus size={20} />
          Add Database
        </Link>
      </div>

      <div className="glass rounded-2xl overflow-hidden border border-border/50">
        <div className="p-6 border-b border-border/50 flex items-center justify-between bg-muted/20">
          <div className="relative w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input 
              type="text" 
              placeholder="Filter connections..." 
              className="w-full bg-muted/50 border border-border rounded-lg py-2 pl-9 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-primary/50 text-foreground"
            />
          </div>
          <div className="text-xs text-muted-foreground">
            Showing {databases.length} connections
          </div>
        </div>

        <div className="divide-y divide-border/50">
          {loading ? (
            <div className="p-20 flex flex-col items-center justify-center gap-4">
              <RefreshCcw className="w-8 h-8 text-primary animate-spin" />
              <p className="text-muted-foreground text-sm">Loading connections...</p>
            </div>
          ) : databases.length === 0 ? (
            <div className="p-20 flex flex-col items-center justify-center text-center gap-4">
              <div className="bg-muted p-4 rounded-full">
                <Database className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground text-sm">No connections found.</p>
              <Link href="/databases/new" className="text-primary text-sm hover:underline">Connect your first database</Link>
            </div>
          ) : (
            databases.map((db, i) => (
              <motion.div
                key={db.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="p-6 hover:bg-muted/30 transition-colors flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center ring-1 ring-primary/20">
                    <Database className="text-primary w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm">{db.name}</h3>
                    <p className="text-xs text-muted-foreground mt-0.5 font-mono">
                      {db.username}@{db.host}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Link
                    href={`/chat/${db.id}`}
                    className="p-2 px-4 rounded-lg bg-background border border-border hover:bg-primary/10 text-xs font-bold transition-all flex items-center gap-2"
                  >
                    <MessageSquare size={14} />
                    Query
                  </Link>
                  <Link
                    href={`/databases/${db.id}`}
                    className="p-2 rounded-lg bg-background border border-border hover:bg-muted transition-all"
                  >
                    <Settings size={16} className="text-muted-foreground" />
                  </Link>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
