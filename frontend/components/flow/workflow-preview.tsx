"use client";

import * as React from "react";
import { ReactFlow, Background, BackgroundVariant } from "@xyflow/react";
import type { AgentSpec } from "@/lib/types";
import { nodeTypes } from "@/components/flow/nodes";
import { specToFlow } from "@/components/flow/graph";
import { cn } from "@/lib/utils";

interface WorkflowPreviewProps {
  spec: AgentSpec;
  className?: string;
}

/** Read-only React Flow render of an AgentSpec workflow. */
export function WorkflowPreview({ spec, className }: WorkflowPreviewProps) {
  const { nodes, edges } = React.useMemo(
    () => specToFlow(spec.workflow, spec),
    [spec]
  );

  return (
    <div className={cn("h-72 w-full overflow-hidden rounded-lg border bg-background", className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        zoomOnScroll={false}
        panOnDrag
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="hsl(240 6% 20%)" />
      </ReactFlow>
    </div>
  );
}
