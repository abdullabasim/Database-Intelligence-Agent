"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Database, 
  LayoutDashboard, 
  Settings, 
  LogOut, 
  ChevronLeft, 
  ChevronRight,
  PlusCircle,
  MessageSquare,
  Activity
} from "lucide-react";
import { authStore, UserSession } from "@/lib/auth-store";
import { cn } from "@/lib/utils";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<UserSession | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const s = authStore.getSession();
    if (!s) {
      router.push("/login");
    } else {
      setSession(s);
    }
  }, [router]);

  const handleLogout = () => {
    authStore.clearSession();
    router.push("/login");
  };

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Databases", href: "/databases", icon: Database },
    { name: "Activity", href: "/activity", icon: Activity },
  ];

  if (!session) return null;

  return (
    <div className="flex min-h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: isCollapsed ? 80 : 260 }}
        className="glass border-r border-border/50 relative z-20 flex flex-col"
      >
        {/* Toggle Button */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3 top-10 bg-primary border border-primary-foreground/20 rounded-full p-1 text-white hover:scale-110 transition-transform z-30"
        >
          {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>

        {/* Logo */}
        <div className="p-6 flex items-center gap-3">
          <div className="bg-primary/20 p-2 rounded-lg ring-1 ring-primary/30 shrink-0">
            <Database className="text-primary w-6 h-6" />
          </div>
          {!isCollapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-bold text-lg tracking-tight"
            >
              DataIntel
            </motion.span>
          )}
        </div>

        {/* Nav Links */}
        <nav className="flex-1 px-4 mt-4 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 p-3 rounded-xl transition-all group relative",
                pathname === item.href 
                  ? "bg-primary/10 text-primary ring-1 ring-primary/20 shadow-sm shadow-primary/10" 
                  : "hover:bg-muted/50 text-muted-foreground hover:text-foreground"
              )}
            >
              <item.icon size={22} className={cn("shrink-0", pathname === item.href ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
              {!isCollapsed && (
                <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  {item.name}
                </motion.span>
              )}
              {pathname === item.href && (
                <motion.div
                  layoutId="activeNav"
                  className="absolute left-0 w-1 h-6 bg-primary rounded-r-full"
                />
              )}
            </Link>
          ))}
        </nav>

        {/* User Profile */}
        <div className="p-4 border-t border-border/50 bg-muted/20">
          <div className={cn("flex items-center gap-3 p-2 rounded-xl", isCollapsed ? "justify-center" : "")}>
            <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center text-accent text-xs font-bold ring-1 ring-accent/30 shrink-0">
              {session.email[0].toUpperCase()}
            </div>
            {!isCollapsed && (
              <div className="flex-1 overflow-hidden">
                <p className="text-xs font-medium truncate">{session.email}</p>
                <p className="text-[10px] text-muted-foreground">Free Plan</p>
              </div>
            )}
          </div>
          <button
            onClick={handleLogout}
            className={cn(
              "w-full flex items-center gap-3 p-2 px-3 mt-2 rounded-xl text-destructive hover:bg-destructive/10 transition-all text-sm",
              isCollapsed ? "justify-center" : ""
            )}
          >
            <LogOut size={18} />
            {!isCollapsed && <span>Logout</span>}
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 relative overflow-y-auto scrollbar-hide">
        {/* Background Gradients */}
        <div className="absolute inset-0 pointer-events-none -z-10 overflow-hidden">
          <div className="absolute top-[20%] left-[10%] w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px]" />
          <div className="absolute bottom-[20%] right-[10%] w-[500px] h-[500px] bg-accent/5 rounded-full blur-[120px]" />
        </div>
        
        <div className="p-8 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
