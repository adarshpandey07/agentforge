"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  FolderKanban,
  Sparkles,
  LayoutTemplate,
  FileText,
  BookOpen,
  Wrench,
  ScrollText,
  Rocket,
  Settings,
  Bot,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_SECTIONS: {
  title: string | null;
  items: { href: string; label: string; icon: typeof LayoutDashboard }[];
}[] = [
  {
    title: null,
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/clients", label: "Clients", icon: Users },
      { href: "/projects", label: "Projects", icon: FolderKanban },
    ],
  },
  {
    title: "Build",
    items: [
      { href: "/generate", label: "Generate", icon: Sparkles },
      { href: "/templates", label: "Templates", icon: LayoutTemplate },
      { href: "/prompts", label: "Prompts", icon: FileText },
      { href: "/knowledge", label: "Knowledge", icon: BookOpen },
      { href: "/tools", label: "Tools", icon: Wrench },
    ],
  },
  {
    title: "Operate",
    items: [
      { href: "/logs", label: "Logs", icon: ScrollText },
      { href: "/deployments", label: "Deployments", icon: Rocket },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

export function SidebarNav() {
  const pathname = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r border-white/[0.06] bg-card/60 backdrop-blur-xl">
      <div className="flex h-14 items-center gap-2.5 border-b border-white/[0.06] px-5">
        <div className="gradient-brand flex h-7 w-7 items-center justify-center rounded-lg shadow-glow">
          <Bot className="h-4 w-4 text-white" />
        </div>
        <span className="text-sm font-semibold tracking-tight">
          Agent<span className="gradient-text">Forge</span>
        </span>
      </div>
      <nav className="flex-1 overflow-y-auto p-3">
        {NAV_SECTIONS.map((section, si) => (
          <div key={si} className={si > 0 ? "mt-5" : undefined}>
            {section.title && (
              <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground/70">
                {section.title}
              </p>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active =
                  pathname === item.href || pathname.startsWith(item.href + "/");
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
                      active
                        ? "bg-primary/10 text-foreground"
                        : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                    )}
                  >
                    {active && (
                      <span className="absolute left-0 top-1/2 h-4 w-[3px] -translate-y-1/2 rounded-r-full bg-gradient-to-b from-violet-400 to-indigo-500" />
                    )}
                    <Icon
                      className={cn(
                        "h-4 w-4 transition-colors",
                        active
                          ? "text-primary"
                          : "text-muted-foreground/80 group-hover:text-foreground"
                      )}
                    />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
      <div className="border-t border-white/[0.06] p-4">
        <div className="flex items-center gap-2">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
          </span>
          <p className="text-[11px] text-muted-foreground">
            All systems operational
          </p>
        </div>
        <p className="mt-1.5 text-[10px] text-muted-foreground/60">
          Agent-as-a-Service · v1.0
        </p>
      </div>
    </aside>
  );
}
