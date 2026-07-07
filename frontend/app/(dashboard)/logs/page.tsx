"use client";

import { useEffect, useState } from "react";
import { ScrollText, Search } from "lucide-react";
import { api } from "@/lib/api";
import type { AuditLog, LlmCall, ToolCallLog } from "@/lib/types";
import { formatCost, formatDate, formatNumber } from "@/lib/utils";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Badge, statusVariant } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TableSkeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function LogsPage() {
  const [tab, setTab] = useState("llm");
  const [query, setQuery] = useState("");
  const [llmCalls, setLlmCalls] = useState<LlmCall[] | null>(null);
  const [toolCalls, setToolCalls] = useState<ToolCallLog[] | null>(null);
  const [audit, setAudit] = useState<AuditLog[] | null>(null);

  useEffect(() => {
    const params = { limit: 100, ...(query ? { q: query } : {}) };
    const t = setTimeout(() => {
      if (tab === "llm") api.logs.llmCalls(params).then(setLlmCalls).catch(() => setLlmCalls([]));
      if (tab === "tools") api.logs.toolCalls(params).then(setToolCalls).catch(() => setToolCalls([]));
      if (tab === "audit") api.logs.auditLogs(params).then(setAudit).catch(() => setAudit([]));
    }, query ? 300 : 0);
    return () => clearTimeout(t);
  }, [tab, query]);

  const filterLlm = (rows: LlmCall[]) =>
    query ? rows.filter((r) => `${r.model} ${r.provider}`.toLowerCase().includes(query.toLowerCase())) : rows;
  const filterTools = (rows: ToolCallLog[]) =>
    query ? rows.filter((r) => r.tool_name.toLowerCase().includes(query.toLowerCase())) : rows;
  const filterAudit = (rows: AuditLog[]) =>
    query ? rows.filter((r) => `${r.actor} ${r.action} ${r.resource}`.toLowerCase().includes(query.toLowerCase())) : rows;

  return (
    <div>
      <PageHeader title="Logs" description="Full observability across models, tools and platform actions." />

      <Tabs value={tab} onValueChange={setTab}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <TabsList>
            <TabsTrigger value="llm">LLM Calls</TabsTrigger>
            <TabsTrigger value="tools">Tool Calls</TabsTrigger>
            <TabsTrigger value="audit">Audit</TabsTrigger>
          </TabsList>
          <div className="relative w-64">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Filter…" className="pl-8" value={query} onChange={(e) => setQuery(e.target.value)} />
          </div>
        </div>

        <TabsContent value="llm">
          {llmCalls === null ? (
            <TableSkeleton rows={8} />
          ) : filterLlm(llmCalls).length === 0 ? (
            <EmptyState icon={ScrollText} title="No LLM calls" description="Calls appear here once agents start talking." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model</TableHead>
                  <TableHead>Provider</TableHead>
                  <TableHead className="text-right">Prompt tok</TableHead>
                  <TableHead className="text-right">Completion tok</TableHead>
                  <TableHead className="text-right">Cost</TableHead>
                  <TableHead className="text-right">Latency</TableHead>
                  <TableHead className="text-right">When</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filterLlm(llmCalls).map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium">{c.model}</TableCell>
                    <TableCell><Badge variant="secondary">{c.provider}</Badge></TableCell>
                    <TableCell className="text-right tabular-nums">{formatNumber(c.prompt_tokens)}</TableCell>
                    <TableCell className="text-right tabular-nums">{formatNumber(c.completion_tokens)}</TableCell>
                    <TableCell className="text-right tabular-nums">{formatCost(c.cost)}</TableCell>
                    <TableCell className="text-right tabular-nums">{c.latency_ms}ms</TableCell>
                    <TableCell className="text-right text-muted-foreground">{formatDate(c.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </TabsContent>

        <TabsContent value="tools">
          {toolCalls === null ? (
            <TableSkeleton rows={8} />
          ) : filterTools(toolCalls).length === 0 ? (
            <EmptyState icon={ScrollText} title="No tool calls" description="When agents call tools you will see inputs, outputs and durations here." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tool</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Input</TableHead>
                  <TableHead className="text-right">Duration</TableHead>
                  <TableHead className="text-right">When</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filterTools(toolCalls).map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium">{c.tool_name}</TableCell>
                    <TableCell>
                      <Badge variant={c.error ? "destructive" : "success"}>{c.error ? "error" : "ok"}</Badge>
                    </TableCell>
                    <TableCell className="max-w-xs truncate text-xs text-muted-foreground">
                      {typeof c.input === "string" ? c.input : JSON.stringify(c.input ?? {})}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{c.duration_ms}ms</TableCell>
                    <TableCell className="text-right text-muted-foreground">{formatDate(c.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </TabsContent>

        <TabsContent value="audit">
          {audit === null ? (
            <TableSkeleton rows={8} />
          ) : filterAudit(audit).length === 0 ? (
            <EmptyState icon={ScrollText} title="No audit events" description="Platform actions (create, update, deploy) are recorded here." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Actor</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead className="text-right">When</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filterAudit(audit).map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="font-medium">{a.actor}</TableCell>
                    <TableCell><Badge variant={statusVariant(a.action)}>{a.action}</Badge></TableCell>
                    <TableCell className="text-muted-foreground">{a.resource}</TableCell>
                    <TableCell className="text-right text-muted-foreground">{formatDate(a.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
