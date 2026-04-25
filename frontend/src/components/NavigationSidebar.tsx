"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, Menu, ChevronLeft, ChevronRight, BarChart2, Users, Info, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { cn } from "@/lib/utils";

export const NavigationSidebar = () => {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const links = [
    { href: "/analyze", label: "Analyze", icon: BarChart2 },
    { href: "/community", label: "Community", icon: Users },
  ];

  const SidebarContent = () => (
    <>
      <div className={cn("h-16 flex items-center px-4 border-b border-border/40 shrink-0", collapsed ? "justify-center" : "justify-between")}>
        {!collapsed && (
          <Link href="/" className="flex items-center gap-2 group min-w-0">
            <span className="font-serif text-xl font-semibold tracking-tight truncate">Veritas</span>
          </Link>
        )}
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-8 w-8 hidden md:flex shrink-0" 
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      <div className="flex-1 py-6 px-3 flex flex-col gap-2 overflow-y-auto">
        <nav className="flex flex-col gap-1">
          {links.map((l) => {
            const isActive = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setMobileOpen(false)}
                title={collapsed ? l.label : undefined}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/50",
                  collapsed && "md:justify-center"
                )}
              >
                <l.icon className="h-5 w-5 shrink-0" />
                <span className={cn(collapsed && "md:hidden")}>{l.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-border/40 shrink-0">
        <Button className={cn("w-full bg-gradient-primary text-primary-foreground shadow-glow", collapsed && "md:px-0")} asChild>
          <Link href="/analyze" title={collapsed ? "New Analysis" : undefined}>
            {collapsed ? <BarChart2 className="h-4 w-4 hidden md:block" /> : null}
            <span className={cn(collapsed && "md:hidden")}>New Analysis</span>
          </Link>
        </Button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile Top Bar (only visible on mobile since we removed top bar) */}
      <div className="md:hidden flex items-center justify-between p-4 border-b border-border/40 bg-background sticky top-0 z-40">
        <Link href="/" className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-primary" />
          <span className="font-serif text-xl font-semibold tracking-tight">Veritas</span>
        </Link>
        <Button variant="ghost" size="icon" onClick={() => setMobileOpen(true)}>
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <aside className="relative w-64 bg-background border-r border-border/40 flex flex-col h-full animate-in slide-in-from-left">
            <Button variant="ghost" size="icon" className="absolute top-3 right-3" onClick={() => setMobileOpen(false)}>
              <X className="h-5 w-5" />
            </Button>
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden md:flex flex-col border-r border-border/40 bg-background h-screen sticky top-0 transition-all duration-300 shrink-0 z-40",
          collapsed ? "w-20" : "w-64"
        )}
      >
        <SidebarContent />
      </aside>
    </>
  );
};
