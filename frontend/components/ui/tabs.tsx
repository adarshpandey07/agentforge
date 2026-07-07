"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface TabsContextValue {
  value: string;
  setValue: (v: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | null>(null);

interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
}

function Tabs({ value, defaultValue, onValueChange, className, children, ...props }: TabsProps) {
  const [internal, setInternal] = React.useState(defaultValue ?? "");
  const current = value !== undefined ? value : internal;
  const setValue = (v: string) => {
    if (value === undefined) setInternal(v);
    onValueChange?.(v);
  };
  return (
    <TabsContext.Provider value={{ value: current, setValue }}>
      <div className={cn("w-full", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
}

function useTabs(): TabsContextValue {
  const ctx = React.useContext(TabsContext);
  if (!ctx) throw new Error("Tabs components must be used within <Tabs>");
  return ctx;
}

function TabsList({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("inline-flex h-9 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground", className)}
      {...props}
    />
  );
}

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

function TabsTrigger({ value, className, ...props }: TabsTriggerProps) {
  const { value: current, setValue } = useTabs();
  const active = current === value;
  return (
    <button
      type="button"
      onClick={() => setValue(value)}
      data-state={active ? "active" : "inactive"}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1 text-sm font-medium transition-all focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
        active ? "bg-background text-foreground shadow" : "hover:text-foreground",
        className
      )}
      {...props}
    />
  );
}

interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
}

function TabsContent({ value, className, ...props }: TabsContentProps) {
  const { value: current } = useTabs();
  if (current !== value) return null;
  return <div className={cn("mt-4 animate-fade-in", className)} {...props} />;
}

export { Tabs, TabsList, TabsTrigger, TabsContent };
