"use client";

import { useCallback, useEffect, useState } from "react";
import { FileText, FlaskConical, GitCommitVertical, Loader2, Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { Prompt, PromptTestResult, PromptVersion } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton, TableSkeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/toast";

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<Prompt[] | null>(null);
  const [selected, setSelected] = useState<Prompt | null>(null);
  const [versions, setVersions] = useState<PromptVersion[] | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [versionOpen, setVersionOpen] = useState(false);
  const [testOpen, setTestOpen] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", content: "" });
  const [versionForm, setVersionForm] = useState({ content: "", notes: "" });
  const [testInput, setTestInput] = useState("");
  const [testResult, setTestResult] = useState<PromptTestResult | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.prompts.list().then(setPrompts).catch(() => setPrompts([]));
  }, []);

  useEffect(load, [load]);

  async function select(p: Prompt) {
    setSelected(p);
    setVersions(null);
    setTestResult(null);
    try {
      const full = await api.prompts.get(p.id);
      setVersions(full.versions ?? p.versions ?? []);
    } catch {
      setVersions(p.versions ?? []);
    }
  }

  async function createPrompt(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.prompts.create(form);
      toast("Prompt created", "success");
      setCreateOpen(false);
      setForm({ name: "", description: "", content: "" });
      load();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Create failed", "error");
    } finally {
      setBusy(false);
    }
  }

  async function createVersion(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setBusy(true);
    try {
      await api.prompts.createVersion(selected.id, versionForm);
      toast("New version saved", "success");
      setVersionOpen(false);
      setVersionForm({ content: "", notes: "" });
      void select(selected);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Version failed", "error");
    } finally {
      setBusy(false);
    }
  }

  async function runTest() {
    if (!selected || !testInput.trim()) return;
    setBusy(true);
    setTestResult(null);
    try {
      const res = await api.prompts.test(selected.id, { input: testInput.trim() });
      setTestResult(res);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Test failed", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Prompts"
        description="Versioned prompt library shared by your agents."
        actions={<Button onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" /> New prompt</Button>}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[320px,1fr]">
        {/* Prompt list */}
        <div className="space-y-2">
          {prompts === null ? (
            <TableSkeleton rows={5} />
          ) : prompts.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No prompts yet"
              description="Create a prompt to start versioning."
              action={<Button size="sm" onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" /> New prompt</Button>}
            />
          ) : (
            prompts.map((p) => (
              <button
                key={p.id}
                onClick={() => void select(p)}
                className={cn(
                  "w-full rounded-lg border bg-card p-3 text-left transition-colors hover:border-primary/50",
                  selected?.id === p.id && "border-primary/70 bg-primary/5"
                )}
              >
                <p className="text-sm font-medium">{p.name}</p>
                <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">
                  {p.description ?? "No description"}
                </p>
                <p className="mt-1 text-[11px] text-muted-foreground">{formatDate(p.updated_at ?? p.created_at)}</p>
              </button>
            ))
          )}
        </div>

        {/* Versions timeline */}
        <div>
          {!selected ? (
            <EmptyState icon={GitCommitVertical} title="Select a prompt" description="Pick a prompt to see its version history and test it." />
          ) : (
            <div>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-base font-semibold">{selected.name}</h2>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" onClick={() => { setTestInput(""); setTestResult(null); setTestOpen(true); }}>
                    <FlaskConical className="h-4 w-4" /> Test
                  </Button>
                  <Button size="sm" onClick={() => { setVersionForm({ content: versions?.[0]?.content ?? "", notes: "" }); setVersionOpen(true); }}>
                    <Plus className="h-4 w-4" /> New version
                  </Button>
                </div>
              </div>

              {versions === null ? (
                <div className="space-y-3"><Skeleton className="h-24" /><Skeleton className="h-24" /></div>
              ) : versions.length === 0 ? (
                <EmptyState icon={GitCommitVertical} title="No versions" description="Save the first version of this prompt." />
              ) : (
                <div className="relative space-y-4 border-l pl-6">
                  {[...versions]
                    .sort((a, b) => b.version - a.version)
                    .map((v, i) => (
                      <div key={v.id} className="relative">
                        <span className="absolute -left-[1.85rem] top-1.5 h-3 w-3 rounded-full border-2 border-background bg-primary" />
                        <div className="rounded-lg border bg-card p-4">
                          <div className="mb-2 flex items-center gap-2">
                            <Badge variant={i === 0 ? "success" : "muted"}>v{v.version}{i === 0 ? " · latest" : ""}</Badge>
                            <span className="text-xs text-muted-foreground">{formatDate(v.created_at)}</span>
                          </div>
                          {v.notes ? <p className="mb-2 text-xs text-muted-foreground">{v.notes}</p> : null}
                          <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded-md bg-background p-3 text-xs text-muted-foreground">
                            {v.content}
                          </pre>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Create prompt */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>New prompt</DialogTitle></DialogHeader>
          <form onSubmit={createPrompt} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="p-name">Name</Label>
              <Input id="p-name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p-desc">Description</Label>
              <Input id="p-desc" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p-content">Initial content</Label>
              <Textarea id="p-content" rows={6} required value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={busy}>Create</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* New version */}
      <Dialog open={versionOpen} onOpenChange={setVersionOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>New version of {selected?.name}</DialogTitle></DialogHeader>
          <form onSubmit={createVersion} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="v-content">Content</Label>
              <Textarea id="v-content" rows={10} required value={versionForm.content} onChange={(e) => setVersionForm({ ...versionForm, content: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="v-notes">Change notes</Label>
              <Input id="v-notes" placeholder="What changed?" value={versionForm.notes} onChange={(e) => setVersionForm({ ...versionForm, notes: e.target.value })} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setVersionOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={busy}>Save version</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Test dialog */}
      <Dialog open={testOpen} onOpenChange={setTestOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Test “{selected?.name}”</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="t-input">Input</Label>
              <Textarea id="t-input" rows={3} placeholder="User message to run through this prompt…" value={testInput} onChange={(e) => setTestInput(e.target.value)} />
            </div>
            <Button onClick={runTest} disabled={busy || !testInput.trim()} className="w-full">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
              Run
            </Button>
            {testResult ? (
              <div className="rounded-md border bg-background p-3">
                <div className="mb-2 flex flex-wrap gap-1.5">
                  {testResult.model ? <Badge variant="secondary">{testResult.model}</Badge> : null}
                  {testResult.latency_ms !== undefined ? <Badge variant="muted">{testResult.latency_ms}ms</Badge> : null}
                  {testResult.stub ? <Badge variant="warning">stub</Badge> : null}
                </div>
                <p className="whitespace-pre-wrap text-sm">{testResult.output}</p>
              </div>
            ) : null}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
