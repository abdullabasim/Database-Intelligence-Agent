"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
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
  AlertCircle,
  Trash2,
  Save,
  RefreshCcw
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { authStore } from "@/lib/auth-store";
import { cn } from "@/lib/utils";

export default function DatabaseDetailsPage() {
  const { id } = useParams();
  const [formData, setFormData] = useState({
    name: "",
    host: "",
    port: 5432,
    db_name: "",
    username: "",
    password: "", // Optional for update
    blocked_tables: ""
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [testStatus, setTestStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const router = useRouter();

  useEffect(() => {
    const fetchDb = async () => {
      const session = authStore.getSession();
      if (!session) return;
      try {
        const data = await api.request<any>(`/databases/${id}`, { auth: { token: session.token } });
        setFormData({
          name: data.name,
          host: data.host,
          port: data.port,
          db_name: data.db_name,
          username: data.username,
          password: "",
          blocked_tables: data.blocked_tables.join(", ")
        });
      } catch (err) {
        console.error(err);
        router.push("/dashboard");
      } finally {
        setLoading(false);
      }
    };
    fetchDb();
  }, [id, router]);

  const handleTest = async () => {
    const session = authStore.getSession();
    if (!session) return;
    setTestStatus("testing");
    try {
      await api.testConnection(id as string, { token: session.token });
      setTestStatus("success");
      setTimeout(() => setTestStatus("idle"), 3000);
    } catch (err: any) {
      setTestStatus("error");
      setError(err.message);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    const session = authStore.getSession();
    if (!session) return;

    try {
      const payload: any = {
        ...formData,
        blocked_tables: formData.blocked_tables.split(",").map(t => t.trim()).filter(Boolean)
      };
      if (!payload.password) delete payload.password;
      
      await api.updateDatabase(id as string, payload, { token: session.token });
      setMessage("Connection updated successfully");
      setTimeout(() => setMessage(""), 3000);
    } catch (err: any) {
      setError(err.message || "Failed to update connection");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this database connection? This action cannot be undone.")) return;
    
    setDeleting(true);
    const session = authStore.getSession();
    if (!session) return;

    try {
      await api.deleteDatabase(id as string, { token: session.token });
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to delete connection");
      setDeleting(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center p-20">
      <RefreshCcw className="animate-spin text-primary" />
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto pb-20">
      <Link href="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-all mb-8 w-fit text-sm group">
        <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
        Back to Dashboard
      </Link>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Database Settings</h1>
          <p className="text-muted-foreground mt-1">Configure your PostgreSQL connection and access rules.</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={handleTest}
            disabled={testStatus === "testing"}
            className={cn(
              "p-2.5 rounded-xl border border-border flex items-center gap-2 text-sm font-medium transition-all shadow-sm",
              testStatus === "success" ? "text-emerald-500 border-emerald-500/30 bg-emerald-500/10" : "hover:bg-muted"
            )}
          >
            {testStatus === "testing" ? <Loader2 size={16} className="animate-spin" /> : <RefreshCcw size={16} />}
            {testStatus === "success" ? "Connected" : "Test Connection"}
          </button>
          
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-2.5 rounded-xl border border-destructive/30 text-destructive bg-destructive/10 hover:bg-destructive/20 flex items-center gap-2 text-sm font-medium transition-all shadow-sm"
          >
            {deleting ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
            Delete
          </button>
        </div>
      </div>

      <form onSubmit={handleUpdate} className="space-y-6">
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
                />
              </div>
            </div>

            <div className="space-y-2 col-span-2">
              <label className="text-sm font-medium text-muted-foreground ml-1">New Password (leave empty to keep current)</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="password"
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
                />
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-border/50 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                 <ShieldCheck className="w-4 h-4 text-primary" />
                 <span className="text-xs text-muted-foreground">Changes take effect immediately.</span>
              </div>
              
              <button
                type="submit"
                disabled={saving}
                className="bg-primary hover:bg-primary/90 text-white px-10 py-3 rounded-2xl font-bold shadow-lg shadow-primary/20 flex items-center gap-2 transition-all disabled:opacity-70"
              >
                {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                Update Settings
              </button>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm text-center">
                {error}
              </div>
            )}
            
            {message && (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-sm text-center">
                {message}
              </div>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
