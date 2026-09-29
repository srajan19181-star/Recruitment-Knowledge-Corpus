"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { MessageSquare, FileText, BarChart3, LogOut } from "lucide-react";

export function Navigation() {
  const pathname = usePathname();
  const router = useRouter();

  if (pathname === "/login" || pathname === "/register") {
    return null;
  }

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch {
      // Ignore network errors on logout
    }
    router.push("/login");
    router.refresh();
  };

  const navItems = [
    { label: "Assistant Chat", href: "/chat", icon: MessageSquare },
    { label: "Recruitment Docs", href: "/documents", icon: FileText },
    { label: "System Analytics", href: "/analytics", icon: BarChart3 },
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <Link href="/chat" className="font-semibold text-slate-900 tracking-tight flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600 inline-block"></span>
            <span>Recruiter Assistant</span>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-normal">AI Copilot</span>
          </Link>

          <nav className="flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                    isActive
                      ? "bg-slate-100 text-blue-600"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <button
          onClick={handleLogout}
          className="text-xs font-medium text-slate-500 hover:text-red-600 transition-colors flex items-center space-x-1 px-2.5 py-1.5 rounded hover:bg-red-50"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </header>
  );
}
