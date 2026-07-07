"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Bot, FlaskConical, Loader2, RefreshCw, Send, User, Workflow as WorkflowIcon, Wrench } from "lucide-react";
import { api } from "@/lib/api";
import type { Agent, ChatToolCall, SimulationReport } from "@/lib/types";
import { cn, formatCost } from "@/lib/utils";
import { Badge, statusVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/toast";

interface Message {
  role: "user" | "assistant";
  content: string;
  tokens?: number;
  cost?: number;
  toolCalls?: ChatToolCall[];
  stub?: boolean;
}

function newSessionId(): string {
  return `sess_${Math.random().toString(36).slice(2, 10)}${Date.now().toString(36)}`;
}

export default function ChatPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [agent, setAgent] = useState<Agent | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState(newSessionId());
  const [sending, setSending] = useState(false);
  const [simOpen, setSimOpen] = useState(false);
  const [scenario, setScenario] = useState("");
  const [simRunning, setSimRunning] = useState(false);
  const [report, setReport] = useState<SimulationReport | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.agents.get(id).then(setAgent).catch(() => setAgent(null));
  }, [id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setSending(true);
    try {
      const res = await api.agents.chat(id, { message: text, session_id: sessionId });
      const totalTokens =
        res.tokens?.total ??
        (res.tokens?.prompt ?? 0) + (res.tokens?.completion ?? 0);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.reply,
          tokens: totalTokens > 0 ? totalTokens : undefined,
          cost: res.cost,
          toolCalls: res.tool_calls,
          stub: res.stub,
        },
      ]);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Chat failed", "error");
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Sorry — the agent runtime returned an error. Check the backend logs." },
      ]);
    } finally {
      setSending(false);
    }
  }

  function reset() {
    setMessages([]);
    setSessionId(newSessionId());
    setReport(null);
  }

  async function runSimulation() {
    if (!scenario.trim()) return;
    setSimRunning(true);
    setReport(null);
    try {
      const rep = await api.agents.simulate(id, { scenario: scenario.trim() });
      setReport(rep);
      setSimOpen(false);
      toast("Simulation complete", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Simulation failed", "error");
    } finally {
      setSimRunning(false);
    }
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-7.5rem)] max-w-4xl flex-col">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link href="/projects" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> Projects
          </Link>
          {agent === null ? (
            <Skeleton className="h-6 w-40" />
          ) : (
            <>
              <span className="text-muted-foreground">/</span>
              <h1 className="text-base font-semibold">{agent.name}</h1>
              <Badge variant={statusVariant(agent.status)}>{agent.status}</Badge>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">session: {sessionId.slice(0, 14)}…</span>
          <Button variant="ghost" size="sm" onClick={reset}>
            <RefreshCw className="h-4 w-4" /> New session
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setSimOpen(true)}>
            <FlaskConical className="h-4 w-4" /> Simulate
          </Button>
          <Link href={`/agents/${id}/builder`}>
            <Button variant="outline" size="sm"><WorkflowIcon className="h-4 w-4" /> Builder</Button>
          </Link>
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto rounded-lg border bg-card/40 p-4">
        {messages.length === 0 && !sending ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary/15">
              <Bot className="h-6 w-6 text-primary" />
            </div>
            <p className="text-sm font-medium">Test playground</p>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Chat with this agent exactly as a customer would. Token usage and tool calls are shown per reply.
            </p>
          </div>
        ) : null}

        {messages.map((m, i) => (
          <div key={i} className={cn("flex gap-3", m.role === "user" ? "justify-end" : "justify-start")}>
            {m.role === "assistant" ? (
              <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                <Bot className="h-4 w-4" />
              </span>
            ) : null}
            <div className={cn("max-w-[75%]")}>
              <div
                className={cn(
                  "whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                  m.role === "user"
                    ? "rounded-br-sm bg-primary text-primary-foreground"
                    : "rounded-bl-sm border bg-card"
                )}
              >
                {m.content}
              </div>
              {m.role === "assistant" && (m.tokens !== undefined || m.cost !== undefined || m.toolCalls?.length || m.stub) ? (
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5 px-1">
                  {m.tokens !== undefined ? (
                    <span className="text-[11px] tabular-nums text-muted-foreground">{m.tokens} tok</span>
                  ) : null}
                  {m.cost !== undefined ? (
                    <span className="text-[11px] tabular-nums text-muted-foreground">· {formatCost(m.cost)}</span>
                  ) : null}
                  {m.stub ? <Badge variant="warning">stub</Badge> : null}
                  {(m.toolCalls ?? []).map((tc, j) => (
                    <Badge key={j} variant={tc.error ? "destructive" : "secondary"}>
                      <Wrench className="h-3 w-3" />
                      {tc.tool_name}
                      {tc.duration_ms !== undefined ? ` · ${tc.duration_ms}ms` : ""}
                    </Badge>
                  ))}
                </div>
              ) : null}
            </div>
            {m.role === "user" ? (
              <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary">
                <User className="h-4 w-4 text-muted-foreground" />
              </span>
            ) : null}
          </div>
        ))}

        {sending ? (
          <div className="flex gap-3">
            <span className="mt-1 flex h-7 w-7 items-center justify-center rounded-full bg-primary/15 text-primary">
              <Bot className="h-4 w-4" />
            </span>
            <div className="rounded-2xl rounded-bl-sm border bg-card px-4 py-3">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          </div>
        ) : null}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
        className="mt-3 flex gap-2"
      >
        <Input
          placeholder="Message the agent…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={sending}
        />
        <Button type="submit" disabled={sending || !input.trim()}>
          <Send className="h-4 w-4" /> Send
        </Button>
      </form>

      {report ? (
        <Card className="mt-4">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Simulation report</CardTitle>
              <div className="flex items-center gap-2">
                {report.score !== undefined ? (
                  <Badge variant={report.score >= 0.7 ? "success" : "warning"}>score {Math.round(report.score * 100)}%</Badge>
                ) : null}
                {report.passed !== undefined ? (
                  <Badge variant={report.passed ? "success" : "destructive"}>{report.passed ? "passed" : "failed"}</Badge>
                ) : null}
                {report.stub ? <Badge variant="warning">stub</Badge> : null}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {report.findings?.length ? (
              <ul className="mb-3 list-inside list-disc space-y-1 text-sm text-muted-foreground">
                {report.findings.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            ) : null}
            {report.transcript?.length ? (
              <div className="max-h-48 space-y-1.5 overflow-y-auto rounded-md border bg-background p-3">
                {report.transcript.map((t, i) => (
                  <p key={i} className="text-xs">
                    <span className="font-semibold text-primary">{t.role}: </span>
                    <span className="text-muted-foreground">{t.content}</span>
                  </p>
                ))}
              </div>
            ) : (
              <pre className="max-h-48 overflow-auto rounded-md border bg-background p-3 text-xs text-muted-foreground">
                {JSON.stringify(report, null, 2)}
              </pre>
            )}
          </CardContent>
        </Card>
      ) : null}

      <Dialog open={simOpen} onOpenChange={setSimOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Run simulation</DialogTitle>
          </DialogHeader>
          <p className="mb-3 text-sm text-muted-foreground">
            Describe a customer scenario. An automated evaluator plays the customer for several turns and grades the agent.
          </p>
          <Textarea
            rows={4}
            placeholder="An angry customer wants to cancel tomorrow's cake order and get a refund…"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setSimOpen(false)}>Cancel</Button>
            <Button onClick={runSimulation} disabled={simRunning || !scenario.trim()}>
              {simRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
              Run
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
