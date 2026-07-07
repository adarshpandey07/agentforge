"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FolderKanban, Search, Sparkles, Bot } from "lucide-react";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Badge, statusVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CardGridSkeleton } from "@/components/ui/skeleton";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const t = setTimeout(() => {
      api.projects
        .list(query ? { q: query } : undefined)
        .then(setProjects)
        .catch(() => setProjects([]));
    }, query ? 300 : 0);
    return () => clearTimeout(t);
  }, [query]);

  return (
    <div>
      <PageHeader
        title="Projects"
        description="Each project bundles the agents, prompts and knowledge for one engagement."
        actions={
          <Link href="/generate">
            <Button><Sparkles className="h-4 w-4" /> Generate agent</Button>
          </Link>
        }
      />

      <div className="mb-4 relative max-w-sm">
        <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input placeholder="Search projects…" className="pl-8" value={query} onChange={(e) => setQuery(e.target.value)} />
      </div>

      {projects === null ? (
        <CardGridSkeleton count={6} />
      ) : projects.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title={query ? "No projects match" : "No projects yet"}
          description={query ? "Try a different search." : "Generate an agent from a requirement, or start from a business template."}
          action={
            !query ? (
              <div className="flex gap-2">
                <Link href="/generate"><Button size="sm"><Sparkles className="h-4 w-4" /> Generate</Button></Link>
                <Link href="/templates"><Button size="sm" variant="secondary">Templates</Button></Link>
              </div>
            ) : undefined
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`}>
              <Card className="h-full transition-colors hover:border-primary/50">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-sm leading-snug">{p.name}</CardTitle>
                    <Badge variant={statusVariant(p.status)}>{p.status}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="line-clamp-2 min-h-[2.5rem] text-sm text-muted-foreground">
                    {p.description ?? "No description"}
                  </p>
                  <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <Bot className="h-3.5 w-3.5" />
                      {p.agent_count ?? 0} agent{(p.agent_count ?? 0) === 1 ? "" : "s"}
                    </span>
                    <span>{formatDate(p.created_at)}</span>
                  </div>
                  {p.client_name ? (
                    <p className="mt-2 text-xs text-muted-foreground">Client: {p.client_name}</p>
                  ) : null}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
