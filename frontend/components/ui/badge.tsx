import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary/15 text-primary",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        outline: "text-foreground",
        success: "border-transparent bg-emerald-500/15 text-emerald-400",
        warning: "border-transparent bg-amber-500/15 text-amber-400",
        destructive: "border-transparent bg-destructive/15 text-red-400",
        muted: "border-transparent bg-muted text-muted-foreground",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

/** Maps common backend status strings to a badge variant. */
export function statusVariant(status: string | undefined | null): BadgeProps["variant"] {
  switch ((status ?? "").toLowerCase()) {
    case "active":
    case "running":
    case "indexed":
    case "connected":
    case "completed":
    case "success":
      return "success";
    case "pending":
    case "building":
    case "processing":
    case "draft":
      return "warning";
    case "failed":
    case "error":
    case "stopped":
      return "destructive";
    case "paused":
    case "archived":
      return "muted";
    default:
      return "secondary";
  }
}

export { Badge, badgeVariants };
