"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  useReactFlow,
  type Connection,
  type Edge,
} from "@xyflow/react";
import { ArrowLeft, Bot, GitBranch, LogIn, LogOut, MessageSquare, Save, Trash2, Wrench, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Agent, WorkflowNodeType } from "@/lib/types";
import { titleCase } from "@/lib/utils";
import { nodeTypes, type ForgeNode } from "@/components/flow/nodes";
import { specToFlow, flowToSpec } from "@/components/flow/graph";
import { Badge, statusVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/toast";

const PALETTE: { type: WorkflowNodeType; label: string; icon: React.ElementType; chip: string }[] = [
  { type: "agent", label: "Agent", icon: Bot, chip: "bg-violet-500/15 text-violet-300" },
  { type: "tool", label: "Tool", icon: Wrench, chip: "bg-sky-500/15 text-sky-300" },
  { type: "condition", label: "Condition", icon: GitBranch, chip: "bg-amber-500/15 text-amber-300" },
  { type: "input", label: "Input", icon: LogIn, chip: "bg-emerald-500/15 text-emerald-300" },
  { type: "output", label: "Output", icon: LogOut, chip: "bg-rose-500/15 text-rose-300" },
];

function BuilderCanvas({ agent, onAgentChange }: { agent: Agent; onAgentChange: (a: Agent) => void }) {
  const initial = useMemo(() => specToFlow(agent.spec?.workflow, agent.spec), [agent]);
  const [nodes, setNodes, onNodesChange] = useNodesState<ForgeNode>(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(initial.edges);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const idCounter = useRef(1000);
  const { screenToFlowPosition } = useReactFlow();

  const selected = nodes.find((n) => n.id === selectedId) ?? null;
  const selectedSpecAgent = selected?.data.ref
    ? agent.spec.agents.find((a) => a.id === selected.data.ref) ?? null
    : null;
  const toolNames = useMemo(
    () => (agent.spec?.tools ?? []).map((t) => t.name),
    [agent]
  );

  const onConnect = useCallback(
    (conn: Connection) => setEdges((eds) => addEdge({ ...conn, animated: true }, eds)),
    [setEdges]
  );

  const addNode = useCallback(
    (type: WorkflowNodeType, position: { x: number; y: number }) => {
      const id = `n${++idCounter.current}`;
      const node: ForgeNode = {
        id,
        type,
        position,
        data: { label: `New ${titleCase(type)}`, nodeType: type },
      };
      setNodes((nds) => [...nds, node]);
      setSelectedId(id);
    },
    [setNodes]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const type = e.dataTransfer.getData("application/agentforge-node") as WorkflowNodeType;
      if (!type) return;
      addNode(type, screenToFlowPosition({ x: e.clientX, y: e.clientY }));
    },
    [addNode, screenToFlowPosition]
  );

  function updateSelected(patch: Partial<ForgeNode["data"]>) {
    if (!selected) return;
    setNodes((nds) =>
      nds.map((n) => (n.id === selected.id ? { ...n, data: { ...n.data, ...patch } } : n))
    );
  }

  function updateSpecAgent(patch: { system_prompt?: string; tools?: string[] }) {
    if (!selectedSpecAgent) return;
    const nextSpec = {
      ...agent.spec,
      agents: agent.spec.agents.map((a) =>
        a.id === selectedSpecAgent.id ? { ...a, ...patch } : a
      ),
    };
    onAgentChange({ ...agent, spec: nextSpec });
  }

  function deleteSelected() {
    if (!selected) return;
    setNodes((nds) => nds.filter((n) => n.id !== selected.id));
    setEdges((eds) => eds.filter((e) => e.source !== selected.id && e.target !== selected.id));
    setSelectedId(null);
  }

  async function save() {
    setSaving(true);
    try {
      const graph = flowToSpec(nodes, edges);
      const nextSpec = { ...agent.spec, workflow: graph };
      await api.agents.update(agent.id, { spec: nextSpec });
      onAgentChange({ ...agent, spec: nextSpec });
      toast("Workflow saved", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Save failed", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-8.5rem)] gap-4">
      {/* Palette */}
      <aside className="w-44 shrink-0 space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Node palette</p>
        {PALETTE.map((p) => (
          <div
            key={p.type}
            draggable
            onDragStart={(e) => {
              e.dataTransfer.setData("application/agentforge-node", p.type);
              e.dataTransfer.effectAllowed = "move";
            }}
            onDoubleClick={() => addNode(p.type, { x: 120, y: 120 })}
            className="flex cursor-grab items-center gap-2 rounded-md border bg-card px-3 py-2 text-sm transition-colors hover:border-primary/50 active:cursor-grabbing"
            title="Drag onto canvas (or double-click)"
          >
            <span className={`flex h-6 w-6 items-center justify-center rounded ${p.chip}`}>
              <p.icon className="h-3.5 w-3.5" />
            </span>
            {p.label}
          </div>
        ))}
        <p className="pt-1 text-[11px] leading-relaxed text-muted-foreground">
          Drag nodes onto the canvas. Connect handles to route the conversation.
        </p>
      </aside>

      {/* Canvas */}
      <div className="min-w-0 flex-1 overflow-hidden rounded-lg border" onDrop={onDrop} onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = "move"; }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={(_, node) => setSelectedId(node.id)}
          onPaneClick={() => setSelectedId(null)}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="hsl(240 6% 20%)" />
          <Controls />
          <MiniMap pannable zoomable nodeColor="hsl(252 60% 40%)" maskColor="rgba(0,0,0,0.5)" />
        </ReactFlow>
      </div>

      {/* Properties */}
      <aside className="w-72 shrink-0 space-y-4 overflow-y-auto rounded-lg border bg-card p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Properties</p>
          <Button size="sm" onClick={save} disabled={saving}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Save
          </Button>
        </div>
        {!selected ? (
          <p className="text-sm text-muted-foreground">Select a node to edit its name, system prompt and tools.</p>
        ) : (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label>Name</Label>
              <Input value={selected.data.label} onChange={(e) => updateSelected({ label: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <Label>Type</Label>
              <Badge variant="secondary">{titleCase(selected.data.nodeType)}</Badge>
              {selected.data.ref ? (
                <p className="text-xs text-muted-foreground">ref: {selected.data.ref}</p>
              ) : null}
            </div>
            {selectedSpecAgent ? (
              <>
                <div className="space-y-1.5">
                  <Label>System prompt</Label>
                  <Textarea
                    rows={8}
                    className="text-xs"
                    value={selectedSpecAgent.system_prompt}
                    onChange={(e) => updateSpecAgent({ system_prompt: e.target.value })}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Tools</Label>
                  <div className="space-y-1">
                    {toolNames.length === 0 ? (
                      <p className="text-xs text-muted-foreground">No tools defined in this spec.</p>
                    ) : (
                      toolNames.map((t) => {
                        const checked = selectedSpecAgent.tools.includes(t);
                        return (
                          <label key={t} className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1 text-sm hover:bg-accent">
                            <input
                              type="checkbox"
                              className="h-3.5 w-3.5 accent-[hsl(var(--primary))]"
                              checked={checked}
                              onChange={(e) =>
                                updateSpecAgent({
                                  tools: e.target.checked
                                    ? [...selectedSpecAgent.tools, t]
                                    : selectedSpecAgent.tools.filter((x) => x !== t),
                                })
                              }
                            />
                            {t}
                          </label>
                        );
                      })
                    )}
                  </div>
                </div>
              </>
            ) : null}
            <Button variant="destructive" size="sm" className="w-full" onClick={deleteSelected}>
              <Trash2 className="h-4 w-4" /> Delete node
            </Button>
          </div>
        )}
      </aside>
    </div>
  );
}

export default function BuilderPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [agent, setAgent] = useState<Agent | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.agents.get(id).then(setAgent).catch((e: Error) => setError(e.message));
  }, [id]);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link href="/projects" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> Projects
          </Link>
          {agent ? (
            <>
              <span className="text-muted-foreground">/</span>
              <h1 className="text-base font-semibold">{agent.name}</h1>
              <Badge variant={statusVariant(agent.status)}>{agent.status}</Badge>
            </>
          ) : null}
        </div>
        <Link href={`/agents/${id}/chat`}>
          <Button variant="secondary" size="sm">
            <MessageSquare className="h-4 w-4" /> Test in playground
          </Button>
        </Link>
      </div>

      {error ? (
        <p className="text-sm text-red-400">Failed to load agent: {error}</p>
      ) : agent === null ? (
        <div className="flex h-[calc(100vh-8.5rem)] gap-4">
          <Skeleton className="w-44" />
          <Skeleton className="flex-1" />
          <Skeleton className="w-72" />
        </div>
      ) : (
        <ReactFlowProvider>
          <BuilderCanvas agent={agent} onAgentChange={setAgent} />
        </ReactFlowProvider>
      )}
    </div>
  );
}
