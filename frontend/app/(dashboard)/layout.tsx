"use client";

import { ChevronDown, LogOut, Settings, User as UserIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { SidebarNav } from "@/components/ui/sidebar-nav";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, authenticated, logout } = useAuth();
  const router = useRouter();

  if (loading && !authenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Skeleton className="h-8 w-40" />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <SidebarNav />
      <div className="pl-60">
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-white/[0.06] bg-background/70 px-6 backdrop-blur-xl">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-violet-400" />
            {user?.tenant_name ?? "Workspace"}
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition-colors duration-150 hover:bg-accent">
              <span className="gradient-brand flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold text-white shadow-[inset_0_1px_0_rgb(255_255_255/0.2)]">
                {(user?.full_name ?? user?.email ?? "U").charAt(0).toUpperCase()}
              </span>
              <span className="max-w-[140px] truncate">
                {user?.full_name ?? user?.email ?? "Account"}
              </span>
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuLabel>
                {user?.email ?? "Signed in"}
                {user?.role ? ` · ${user.role}` : ""}
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/settings")}>
                <UserIcon className="h-4 w-4" /> Profile
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => router.push("/settings")}>
                <Settings className="h-4 w-4" /> Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="text-red-400">
                <LogOut className="h-4 w-4" /> Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
