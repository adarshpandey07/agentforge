"use client";

import { useCallback, useEffect, useState } from "react";
import { ExternalLink, Loader2, Rocket } from "lucide-react";
import { api } from "@/lib/api";
import type { Agent, Deployment } from "@/lib/types";
import { formatDate, titleCase } from "@/lib/utils";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Badge, statusVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { TableSkeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toast";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const MODES = [
  { value: "docker", label: "Docker — container image + compose file" },
  { value: "cloud", label: "Cloud — managed AgentForge cloud" },
  { value: "vps", label: "VPS — provision to a client server" },
  { value: "local", label: "Local — run on this machine" },
];

export default function DeploymentsPage() {
  const [deployments, setDeployments] = useState<Deployment[] | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [open, setOpen] = useState(false);
  const [agentId, setAgentId] = useState("");
  const [mode, setMode] = useState("docker");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.deployments.list().then(setDeployments).catch(() => setDeployments([]));
  }, []);

  useEffect(() => {
    load();
    api.agents.list().then(setAgents).catch(() => setAgents([]));
  }, [load]);

  async function deploy(e: React.FormEvent) {
    e.preventDefault();
    if (!agentId) return;
    setBusy(true);
    try {
      await api.deployments.create({ agent_id: agentId, mode });
      toast("Deployment started", "success");
      setOpen(false);
      load();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Deployment failed", "error");
    } finally {
      setBusy(false);
    }
  }

  function agentName(dep: Deployment): string {
    return dep.agent_name ?? agents.find((a) => a.id === dep.agent_id)?.name ?? dep.agent_id;
  }

  return (
    <div>
      <PageHeader
        title="Deployments"
        description="Ship agents to production — Docker, cloud, VPS or local."
        actions={
          <Button onClick={() => { setAgentId(agents[0]?.id ?? ""); setOpen(true); }}>
            <Rocket className="h-4 w-4" /> Deploy
          </Button>
        }
      />

      {deployments === null ? (
        <TableSkeleton rows={6} />
      ) : deployments.length === 0 ? (
        <EmptyState
          icon={Rocket}
          title="Nothing deployed yet"
          description="Deploy an agent to give your client a live endpoint."
          action={
            <Button size="sm" onClick={() => { setAgentId(agents[0]?.id ?? ""); setOpen(true); }}>
              <Rocket className="h-4 w-4" /> Deploy an agent
            </Button>
          }
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Agent</TableHead>
              <TableHead>Mode</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>URL</TableHead>
              <TableHead className="text-right">Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {deployments.map((d) => (
              <TableRow key={d.id}>
                <TableCell className="font-medium">{agentName(d)}</TableCell>
                <TableCell><Badge variant="secondary">{titleCase(d.mode)}</Badge></TableCell>
                <TableCell><Badge variant={statusVariant(d.status)}>{d.status}</Badge></TableCell>
                <TableCell>
                  {d.url ? (
                    <a href={d.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-primary hover:underline">
                      {d.url} <ExternalLink className="h-3 w-3" />
                    </a>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell className="text-right text-muted-foreground">{formatDate(d.created_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Deploy an agent</DialogTitle></DialogHeader>
          <form onSubmit={deploy} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="dep-agent">Agent</Label>
              <Select id="dep-agent" required value={agentId} onChange={(e) => setAgentId(e.target.value)}>
                <option value="">Select an agent…</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="dep-mode">Mode</Label>
              <Select id="dep-mode" value={mode} onChange={(e) => setMode(e.target.value)}>
                {MODES.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={busy || !agentId}>
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
                Deploy
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
