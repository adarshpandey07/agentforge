"use client";

import * as React from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastVariant = "success" | "error" | "info";

interface ToastItem {
  id: number;
  message: string;
  variant: ToastVariant;
}

type Listener = (t: ToastItem) => void;

let listeners: Listener[] = [];
let counter = 0;

/** Fire a toast from anywhere (no provider required beyond <Toaster/> in the layout). */
export function toast(message: string, variant: ToastVariant = "info"): void {
  const item = { id: ++counter, message, variant };
  listeners.forEach((l) => l(item));
}

const icons: Record<ToastVariant, React.ReactNode> = {
  success: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
  error: <AlertCircle className="h-4 w-4 text-red-400" />,
  info: <Info className="h-4 w-4 text-sky-400" />,
};

export function Toaster() {
  const [toasts, setToasts] = React.useState<ToastItem[]>([]);

  React.useEffect(() => {
    const listener: Listener = (t) => {
      setToasts((prev) => [...prev, t]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((x) => x.id !== t.id));
      }, 4500);
    };
    listeners.push(listener);
    return () => {
      listeners = listeners.filter((l) => l !== listener);
    };
  }, []);

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-80 flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "pointer-events-auto flex items-start gap-2 rounded-lg border bg-popover p-3 text-sm shadow-lg animate-fade-in"
          )}
        >
          <span className="mt-0.5">{icons[t.variant]}</span>
          <span className="flex-1 leading-snug">{t.message}</span>
          <button
            onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
            className="text-muted-foreground hover:text-foreground"
            aria-label="Dismiss"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}
