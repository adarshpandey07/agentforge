"use client";

import { useState } from "react";
import Link from "next/link";
import { Sparkles, Loader2, Bot, Wrench, Brain, ArrowRight, Users } from "lucide-react";
import { api } from "@/lib/api";
import type { AgentSpec } from "@/lib/types";
import { titleCase } from "@/lib/utils";
import { BUSINESS_TYPES, BUSINESS_TYPE_LABELS } from "@/lib/constants";
import { WorkflowPreview } from "@/components/flow/workflow-preview";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/toast";

const EXAMPLES = [
  "Create an AI agent for a bakery that answers questions about the menu, takes custom cake orders and books pickup slots.",
  "A dental clinic needs a receptionist that triages emergencies, books appointments and sends reminders on WhatsApp.",
  "Build a sales agent for a real estate agency that qualifies leads and schedules property viewings.",
];

const MEMORY_LABELS: Record<string, string> = {
  short_term: "Short-term",
  long_term: "Long-term",
  vector: "Vector",
  session: "Session",
  customer: "Customer",
};

export default function GeneratePage() {
  const [prompt, setPrompt] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [loading, setLoading] = useState(false);
  const [spec, setSpec] = useState<(AgentSpec & { agent_id?: string; project_id?: string }) | null>(null);

  async function generate() {
    if (!prompt.trim()) {
      toast("Describe the agent you need first", "info");
      return;
    }
    setLoading(true);
    setSpec(null);
    try {
      const result = await api.generate({
        prompt: prompt.trim(),
        business_type: businessType || undefined,
      });
      setSpec(result);
      toast("Agent spec generated", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Generation failed", "error");
    } finally {
      setLoading(false);
    }
  }

  const memoryEntries = spec?.memory
    ? Object.entries(spec.memory).filter(([, v]) => v)
    : [];

  return (
    <div className="mx-auto max-w-5xl">
      <div className="relative mb-8 flex flex-col items-center pt-6 text-center">
        <div className="bg-grid pointer-events-none absolute inset-x-0 -top-6 h-48 [mask-image:radial-gradient(ellipse_50%_80%_at_50%_0%,black,transparent)]" />
        <div className="gradient-brand animate-fade-up relative mb-4 flex h-12 w-12 items-center justify-center rounded-2xl shadow-glow">
          <Sparkles className="h-5 w-5 text-white" />
        </div>
        <h1 className="animate-fade-up relative text-3xl font-semibold tracking-tighter [animation-delay:60ms]">
          What should your <span className="gradient-text">agent team</span> do?
        </h1>
        <p className="animate-fade-up relative mt-2 max-w-xl text-sm text-muted-foreground [animation-delay:120ms]">
          Describe the business requirement in plain language — AgentForge designs
          the agent team, tools and workflow.
        </p>
      </div>

      <div className="animate-fade-up rounded-xl bg-gradient-to-b from-violet-500/40 via-white/[0.08] to-white/[0.05] p-px shadow-glow [animation-delay:180ms]">
        <Card className="rounded-[calc(0.625rem+3px)] border-transparent shadow-none hover:border-transparent hover:shadow-none">
        <CardContent className="pt-5">
          <Textarea
            rows={4}
            className="text-base"
            placeholder='Create an AI agent for a bakery that takes orders, answers menu questions and books cake pickups…'
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
            <div className="w-56 space-y-1.5">
              <Label htmlFor="btype">Business type (optional)</Label>
              <Select id="btype" value={businessType} onChange={(e) => setBusinessType(e.target.value)}>
                <option value="">Auto-detect</option>
                {BUSINESS_TYPES.map((t) => (
                  <option key={t} value={t}>{BUSINESS_TYPE_LABELS[t]}</option>
                ))}
              </Select>
            </div>
            <Button size="lg" onClick={generate} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              {loading ? "Designing your agent…" : "Generate"}
            </Button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                onClick={() => setPrompt(ex)}
                className="rounded-full border px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
              >
                {ex.slice(0, 56)}…
              </button>
            ))}
          </div>
        </CardContent>
        </Card>
      </div>

      {loading ? (
        <div className="mt-8 space-y-4">
          <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4 animate-pulse-glow text-violet-400" />
            <span className="animate-pulse-glow">
              Designing your agent team — roles, tools, memory, workflow…
            </span>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
          </div>
          <Skeleton className="h-72 w-full" />
        </div>
      ) : null}

      {spec ? (
        <div className="mt-8 space-y-6 animate-fade-in">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold">{spec.name}</h2>
                {spec.business_type ? (
                  <Badge variant="secondary">
                    {BUSINESS_TYPE_LABELS[spec.business_type] ?? titleCase(spec.business_type)}
                  </Badge>
                ) : null}
                {spec.stub ? <Badge variant="warning">stub (no API key)</Badge> : null}
              </div>
              <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{spec.description}</p>
            </div>
            {spec.agent_id ? (
              <Link href={`/agents/${spec.agent_id}/builder`}>
                <Button>
                  Open in Builder <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            ) : (
              <Link href="/projects">
                <Button variant="secondary">
                  View projects <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            )}
          </div>

          <div>
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
              <Users className="h-4 w-4" /> Agent team ({spec.agents.length})
            </h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {spec.agents.map((a) => (
                <Card key={a.id}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center gap-2">
                      <span className="flex h-8 w-8 items-center justify-center rounded-md bg-violet-500/15 text-violet-300">
                        <Bot className="h-4 w-4" />
                      </span>
                      <div>
                        <CardTitle className="text-sm">{a.role}</CardTitle>
                        <CardDescription className="text-xs">model: {a.model}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="line-clamp-3 text-xs text-muted-foreground">{a.system_prompt}</p>
                    <div className="mt-3 flex flex-wrap gap-1">
                      {a.tools.map((t) => (
                        <Badge key={t} variant="default"><Wrench className="h-3 w-3" />{t}</Badge>
                      ))}
                      {a.memory.map((m) => (
                        <Badge key={m} variant="muted"><Brain className="h-3 w-3" />{MEMORY_LABELS[m] ?? m}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Tools & integrations</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {spec.tools.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No external tools required.</p>
                  ) : (
                    spec.tools.map((t) => (
                      <Badge key={t.name} variant="secondary">
                        <Wrench className="h-3 w-3" />
                        {t.name}
                        {t.provider ? <span className="text-muted-foreground">· {t.provider}</span> : null}
                      </Badge>
                    ))
                  )}
                </div>
                {spec.integrations?.length ? (
                  <p className="mt-3 text-xs text-muted-foreground">
                    Channels: {spec.integrations.map(titleCase).join(", ")}
                  </p>
                ) : null}
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Memory & RAG</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {memoryEntries.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Stateless agent.</p>
                  ) : (
                    memoryEntries.map(([k]) => (
                      <Badge key={k} variant="muted"><Brain className="h-3 w-3" />{MEMORY_LABELS[k] ?? k}</Badge>
                    ))
                  )}
                </div>
                {spec.rag?.enabled ? (
                  <p className="mt-3 text-xs text-muted-foreground">
                    RAG enabled · {spec.rag.vector_store ?? "pgvector"} · {spec.rag.embedding_model ?? "default embeddings"}
                  </p>
                ) : (
                  <p className="mt-3 text-xs text-muted-foreground">RAG disabled</p>
                )}
              </CardContent>
            </Card>
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold text-muted-foreground">Workflow preview</h3>
            <WorkflowPreview spec={spec} className="h-80" />
          </div>
        </div>
      ) : null}
    </div>
  );
}
