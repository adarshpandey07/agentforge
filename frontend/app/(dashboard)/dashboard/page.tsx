"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Users, Bot, DollarSign, Cpu, Sparkles, Activity } from "lucide-react";
import { api } from "@/lib/api";
import type { AnalyticsOverview, LlmCall } from "@/lib/types";
import { formatCost, formatNumber, formatDate } from "@/lib/utils";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton, TableSkeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function DashboardPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [calls, setCalls] = useState<LlmCall[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.analytics
      .overview()
      .then((o) => {
        setOverview(o);
        if (o.recent_llm_calls) setCalls(o.recent_llm_calls);
      })
      .catch((e: Error) => setError(e.message));
    api.logs
      .llmCalls({ limit: 8 })
      .then((c) => setCalls((prev) => prev ?? c))
      .catch(() => setCalls((prev) => prev ?? []));
  }, []);

  const stats = [
    { label: "Clients", value: overview ? formatNumber(overview.clients) : null, icon: Users, hint: "businesses onboarded" },
    { label: "Active agents", value: overview ? formatNumber(overview.active_agents ?? overview.agents) : null, icon: Bot, hint: "running across projects" },
    { label: "Total cost", value: overview ? formatCost(overview.total_cost) : null, icon: DollarSign, hint: "LLM spend to date" },
    { label: "Tokens used", value: overview ? formatNumber(overview.total_tokens) : null, icon: Cpu, hint: "prompt + completion" },
  ];

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Your agency at a glance."
        actions={
          <Link href="/generate">
            <Button>
              <Sparkles className="h-4 w-4" /> Generate agent
            </Button>
          </Link>
        }
      />

      {error ? (
        <p className="mb-4 rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
          Could not load analytics: {error}
        </p>
      ) : null}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s, i) => (
          <Card
            key={s.label}
            className="animate-fade-up relative overflow-hidden"
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <div className="pointer-events-none absolute -right-6 -top-6 h-20 w-20 rounded-full bg-primary/[0.07] blur-2xl" />
            <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-[13px] font-medium text-muted-foreground">{s.label}</CardTitle>
              <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/[0.06] bg-white/[0.03]">
                <s.icon className="h-4 w-4 text-violet-300" />
              </span>
            </CardHeader>
            <CardContent>
              {s.value === null ? (
                <Skeleton className="h-8 w-20" />
              ) : (
                <p className="text-2xl font-semibold tracking-tight tabular-nums">{s.value}</p>
              )}
              <p className="mt-1 text-xs text-muted-foreground">{s.hint}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-6">
        <h2 className="mb-3 text-sm font-semibold text-muted-foreground">Recent LLM calls</h2>
        {calls === null ? (
          <TableSkeleton rows={5} />
        ) : calls.length === 0 ? (
          <EmptyState
            icon={Activity}
            title="No activity yet"
            description="Generate an agent and chat with it in the playground — calls will show up here."
            action={
              <Link href="/generate">
                <Button variant="secondary" size="sm">Generate your first agent</Button>
              </Link>
            }
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Model</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead className="text-right">Tokens</TableHead>
                <TableHead className="text-right">Cost</TableHead>
                <TableHead className="text-right">Latency</TableHead>
                <TableHead className="text-right">When</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {calls.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.model}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{c.provider}</Badge>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatNumber(c.prompt_tokens + c.completion_tokens)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{formatCost(c.cost)}</TableCell>
                  <TableCell className="text-right tabular-nums">{c.latency_ms}ms</TableCell>
                  <TableCell className="text-right text-muted-foreground">{formatDate(c.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
