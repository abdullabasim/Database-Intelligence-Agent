"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { 
  ArrowLeft, 
  Database, 
  ShieldCheck, 
  Server, 
  User, 
  Lock, 
  Globe, 
  Loader2,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { authStore } from "@/lib/auth-store";

export default function NewDatabasePage() {
  const [formData, setFormData] = useState({
    name: "",
    host: "",
    port: 5432,
    db_name: "",
    username: "",
    password: "",
    blocked_tables: "users,passwords,tokens,mdl_schemas,sessions"
  });
  const [loading, setLoading] = useState(false);
  const [testStatus, setTestStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleTest = async () => {
    // We can only test after creating for now based on current API, 
    // but we can simulate validation. 
    // Implementation note: The real test happens after ID is generated.
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    const session = authStore.getSession();
    if (!session) return;

    try {
      const payload = {
        ...formData,
        blocked_tables: formData.blocked_tables.split(",").map(t => t.trim()).filter(Boolean)
      };
      await api.createDatabase(payload, { token: session.token });
      router.push("/dashboard?created=true");
    } catch (err: any) {
      setError(err.message || "Failed to create connection");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto pb-20">
      <Link href="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-all mb-8 w-fit text-sm group">
        <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
        Back to Dashboard
      </Link>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Add New Connection</h1>
          <p className="text-muted-foreground mt-1">Connect a PostgreSQL database to start indexing its metadata.</p>
        </div>
        <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center ring-1 ring-primary/20">
          <Database className="text-primary w-6 h-6" />
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="glass p-8 rounded-3xl border border-border/50 shadow-xl space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2 col-span-2">
              <label className="text-sm font-medium text-muted-foreground ml-1">Friendly Connection Name</label>
              <div className="relative">
                <Database className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-muted/30 border border-border rounded-xl py-2.5 pl-10 pr-4 focus:outline-none focus:ring-1 focus:ring-primary/50 text-foreground"
                  placeholder="e.g. Production Data"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground ml-1">Host / Server Address</label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  required
                  value={formData.host}
                  onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                  className="w-full bg-muted/30 border border-border rounded-xl py-2.5 pl-10 pr-4 focus:outline-none focus:ring-1 focus:ring-primary/50 text-foreground"
                  placeholder="db.example.com"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground ml-1">Port</label>
              <div className="relative">
                <Server className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="number"
                  required
                  value={formData.port}
                  onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) })}
                  className="w-full bg-muted/30 border border-border rounded-xl py-2.5 pl-10 pr-4 focus:outline-none focus:ring-1 focus:ring-primary/50 text-foreground"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground ml-1">Database Name</label>
              <div className="relative">
                <Database className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  required
                  value={formData.db_name}
                  onChange={(e) => setFormData({ ...formData, db_name: e.target.value })}
                  className="w-full bg-muted/30 border border-border rounded-xl py-2.5 pl-10 pr-4 focus:outline-none focus:ring-1 focus:ring-primary/50 text-foreground"
                  placeholder="finance_db"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground ml-1">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  required
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="w-full bg-muted/30 border border-border rounded-xl py-2.5 pl-10 pr-4 focus:outline-none focus:ring-1 focus:ring-primary/50 text-foreground"
                  placeholder="readonly_user"
                />
              </div>
            </div>

            <div className="space-y-2 col-span-2">
              <label className="text-sm font-medium text-muted-foreground ml-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full bg-muted/30 border border-border rounded-xl py-2.5 pl-10 pr-4 focus:outline-none focus:ring-1 focus:ring-primary/50 text-foreground"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="space-y-2 col-span-2">
              <label className="text-sm font-medium text-muted-foreground ml-1">Blocked Tables (CSV)</label>
              <div className="relative">
                <ShieldCheck className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  value={formData.blocked_tables}
                  onChange={(e) => setFormData({ ...formData, blocked_tables: e.target.value })}
                  className="w-full bg-muted/30 border border-border rounded-xl py-2.5 pl-10 pr-4 focus:outline-none focus:ring-1 focus:ring-primary/50 text-foreground"
                  placeholder="e.g. users, tokens, audits"
                />
              </div>
              <p className="text-[10px] text-muted-foreground ml-1">
                The AI agent will never be able to see or query these tables.
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-border/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
               {testStatus === "testing" && <Loader2 className="animate-spin w-4 h-4 text-primary" />}
               {testStatus === "success" && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
               {testStatus === "error" && <AlertCircle className="w-4 h-4 text-destructive" />}
               <span className="text-xs text-muted-foreground">Verify connection string before saving.</span>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="px-4 py-2 rounded-xl text-sm font-medium hover:bg-muted transition-all"
                onClick={() => router.back()}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="bg-primary hover:bg-primary/90 text-white px-8 py-2.5 rounded-xl font-bold shadow-lg shadow-primary/20 flex items-center gap-2 transition-all disabled:opacity-70"
              >
                {loading && <Loader2 size={18} className="animate-spin" />}
                Save Connection
              </button>
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm text-center">
              {error}
            </div>
          )}
        </div>
      </form>
    </div>
  );
}
