"use client";

import { motion } from "framer-motion";
import { Activity, Clock, CheckCircle2, RefreshCcw } from "lucide-react";

export default function ActivityPage() {
  const activities = [
    { id: 1, type: "MDL_REFRESH", db: "Production DB", status: "Success", time: "2 hours ago" },
    { id: 2, type: "QUERY", db: "Sales Data", status: "Success", time: "3 hours ago" },
    { id: 3, type: "DB_ADDED", db: "Analytics Replica", status: "Success", time: "1 day ago" },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Recent Activity</h1>
        <p className="text-muted-foreground mt-1">Monitor background tasks and agent operations.</p>
      </div>

      <div className="glass rounded-2xl border border-border/50 overflow-hidden">
        <div className="divide-y divide-border/50">
          {activities.map((act, i) => (
            <motion.div
              key={act.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="p-6 flex items-center justify-between hover:bg-muted/20 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  {act.type === "MDL_REFRESH" ? <RefreshCcw size={18} className="text-primary" /> : <Activity size={18} className="text-primary" />}
                </div>
                <div>
                  <p className="text-sm font-bold">{act.type.replace("_", " ")}</p>
                  <p className="text-xs text-muted-foreground">{act.db}</p>
                </div>
              </div>
              
              <div className="text-right">
                <div className="flex items-center gap-1.5 text-xs text-emerald-500 font-medium bg-emerald-500/10 px-2 py-0.5 rounded-full ring-1 ring-emerald-500/20">
                  <CheckCircle2 size={12} />
                  {act.status}
                </div>
                <div className="flex items-center gap-1 text-[10px] text-muted-foreground mt-1.5">
                  <Clock size={10} />
                  {act.time}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
      
      <div className="p-12 text-center glass border-dashed border-border/50 rounded-2xl">
        <p className="text-sm text-muted-foreground italic">Extended history logging is available in the Pro version.</p>
      </div>
    </div>
  );
}
