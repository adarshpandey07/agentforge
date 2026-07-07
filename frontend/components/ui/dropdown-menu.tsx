"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface DropdownContextValue {
  open: boolean;
  setOpen: (v: boolean) => void;
}

const DropdownContext = React.createContext<DropdownContextValue | null>(null);

function DropdownMenu({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  return (
    <DropdownContext.Provider value={{ open, setOpen }}>
      <div className="relative inline-block" ref={ref}>
        {children}
      </div>
    </DropdownContext.Provider>
  );
}

function useDropdown(): DropdownContextValue {
  const ctx = React.useContext(DropdownContext);
  if (!ctx) throw new Error("DropdownMenu components must be used within <DropdownMenu>");
  return ctx;
}

function DropdownMenuTrigger({ className, children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { open, setOpen } = useDropdown();
  return (
    <button type="button" className={className} onClick={() => setOpen(!open)} {...props}>
      {children}
    </button>
  );
}

function DropdownMenuContent({ className, align = "end", ...props }: React.HTMLAttributes<HTMLDivElement> & { align?: "start" | "end" }) {
  const { open } = useDropdown();
  if (!open) return null;
  return (
    <div
      className={cn(
        "absolute z-50 mt-2 min-w-[10rem] animate-fade-in rounded-md border bg-popover p-1 text-popover-foreground shadow-lg",
        align === "end" ? "right-0" : "left-0",
        className
      )}
      {...props}
    />
  );
}

function DropdownMenuItem({ className, onClick, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  const { setOpen } = useDropdown();
  return (
    <div
      role="menuitem"
      className={cn(
        "flex cursor-pointer select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground",
        className
      )}
      onClick={(e) => {
        onClick?.(e);
        setOpen(false);
      }}
      {...props}
    />
  );
}

function DropdownMenuSeparator({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("-mx-1 my-1 h-px bg-border", className)} {...props} />;
}

function DropdownMenuLabel({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-2 py-1.5 text-xs font-medium text-muted-foreground", className)} {...props} />;
}

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
};
