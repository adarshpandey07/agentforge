import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatCost(cost: number | null | undefined): string {
  if (cost === null || cost === undefined) return "$0.00";
  return cost < 0.01 && cost > 0 ? `$${cost.toFixed(4)}` : `$${cost.toFixed(2)}`;
}

export function formatNumber(n: number | null | undefined): string {
  if (n === null || n === undefined) return "0";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function titleCase(s: string): string {
  return s
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
