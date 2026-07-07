"use client";

import * as React from "react";
import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import { Bot, Wrench, GitBranch, LogIn, LogOut, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { WorkflowNodeType } from "@/lib/types";

export type ForgeNodeData = {
  label: string;
  sublabel?: string;
  nodeType: WorkflowNodeType;
  ref?: string;
};

export type ForgeNode = Node<ForgeNodeData>;

const NODE_STYLES: Record<
  WorkflowNodeType,
  { icon: LucideIcon; accent: string; chip: string; title: string }
> = {
  agent: { icon: Bot, accent: "border-violet-500/50", chip: "bg-violet-500/15 text-violet-300", title: "Agent" },
  tool: { icon: Wrench, accent: "border-sky-500/50", chip: "bg-sky-500/15 text-sky-300", title: "Tool" },
  condition: { icon: GitBranch, accent: "border-amber-500/50", chip: "bg-amber-500/15 text-amber-300", title: "Condition" },
  input: { icon: LogIn, accent: "border-emerald-500/50", chip: "bg-emerald-500/15 text-emerald-300", title: "Input" },
  output: { icon: LogOut, accent: "border-rose-500/50", chip: "bg-rose-500/15 text-rose-300", title: "Output" },
};

function BaseNode({ data, selected }: NodeProps<ForgeNode>) {
  const style = NODE_STYLES[data.nodeType] ?? NODE_STYLES.agent;
  const Icon = style.icon;
  return (
    <div
      className={cn(
        "min-w-[160px] rounded-lg border bg-card px-3 py-2.5 shadow-md transition-shadow",
        style.accent,
        selected && "ring-2 ring-ring"
      )}
    >
      {data.nodeType !== "input" && (
        <Handle type="target" position={Position.Left} />
      )}
      <div className="flex items-center gap-2">
        <span className={cn("flex h-7 w-7 shrink-0 items-center justify-center rounded-md", style.chip)}>
          <Icon className="h-3.5 w-3.5" />
        </span>
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold leading-tight">{data.label}</p>
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
            {data.sublabel ?? style.title}
          </p>
        </div>
      </div>
      {data.nodeType !== "output" && (
        <Handle type="source" position={Position.Right} />
      )}
    </div>
  );
}

export const nodeTypes = {
  agent: BaseNode,
  tool: BaseNode,
  condition: BaseNode,
  input: BaseNode,
  output: BaseNode,
};
