import type { Edge } from "@xyflow/react";
import type { AgentSpec, WorkflowEdge, WorkflowNode, WorkflowNodeType } from "@/lib/types";
import type { ForgeNode } from "@/components/flow/nodes";
import { titleCase } from "@/lib/utils";

/** Convert an AgentSpec workflow graph into React Flow nodes/edges. */
export function specToFlow(
  workflow: { nodes: WorkflowNode[]; edges: WorkflowEdge[] } | undefined,
  spec?: AgentSpec
): { nodes: ForgeNode[]; edges: Edge[] } {
  const wfNodes = workflow?.nodes ?? [];
  const wfEdges = workflow?.edges ?? [];

  const nodes: ForgeNode[] = wfNodes.map((n, i) => {
    const specAgent = spec?.agents.find((a) => a.id === n.ref);
    const label =
      n.label ??
      specAgent?.role ??
      (n.ref ? titleCase(n.ref) : titleCase(n.type));
    return {
      id: n.id,
      type: n.type,
      position: n.position ?? { x: i * 220, y: 80 },
      data: {
        label,
        nodeType: n.type,
        ref: n.ref ?? undefined,
        sublabel: n.ref && specAgent ? titleCase(n.type) : undefined,
      },
    };
  });

  const edges: Edge[] = wfEdges.map((e, i) => ({
    id: `e-${e.source}-${e.target}-${i}`,
    source: e.source,
    target: e.target,
    animated: true,
    label: e.condition ?? undefined,
  }));

  return { nodes, edges };
}

/** Convert React Flow state back into the AgentSpec workflow shape. */
export function flowToSpec(
  nodes: ForgeNode[],
  edges: Edge[]
): { nodes: WorkflowNode[]; edges: WorkflowEdge[] } {
  return {
    nodes: nodes.map((n) => ({
      id: n.id,
      type: (n.type ?? "agent") as WorkflowNodeType,
      ref: n.data.ref ?? null,
      label: n.data.label,
      position: { x: Math.round(n.position.x), y: Math.round(n.position.y) },
    })),
    edges: edges.map((e) => ({
      source: e.source,
      target: e.target,
      condition: typeof e.label === "string" && e.label ? e.label : null,
    })),
  };
}
