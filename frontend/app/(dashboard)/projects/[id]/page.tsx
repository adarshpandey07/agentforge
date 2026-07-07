"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Bot, MessageSquare, Workflow as WorkflowIcon } from "lucide-react";
import { api } from "@/lib/api";
import type { Agent, Project } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { EmptyState } from "@/components/empty-state";
import { Badge, statusVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton, CardGridSkeleton } from "@/components/ui/skeleton";

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [project, setProject] = useState<Project | null>(null);
  const [agents, setAgents] = useState<Agent[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.projects.get(id).then(setProject).catch((e: Error) => setError(e.message));
    api.agents
      .list({ project_id: id })
      .then((all) => setAgents(all.filter((a) => a.project_id === id || !a.project_id)))
      .catch(() => setAgents([]));
  }, [id]);

  if (error) return <p className="text-sm text-red-400">Failed to load project: {error}</p>;

  return (
    <div>
      <Link href="/projects" className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to projects
      </Link>

      {project === null ? (
        <Skeleton className="mb-6 h-16 w-96" />
      ) : (
        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold tracking-tight">{project.name}</h1>
              <Badge variant={statusVariant(project.status)}>{project.status}</Badge>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {project.description ?? "No description"} · created {formatDate(project.created_at)}
            </p>
          </div>
          <Link href="/generate">
            <Button variant="secondary">Add agent</Button>
          </Link>
        </div>
      )}

      <h2 className="mb-3 text-sm font-semibold text-muted-foreground">Agents</h2>
      {agents === null ? (
        <CardGridSkeleton count={3} />
      ) : agents.length === 0 ? (
        <EmptyState
          icon={Bot}
          title="No agents in this project"
          description="Generate one from a requirement or instantiate a template."
          action={<Link href="/generate"><Button size="sm">Generate agent</Button></Link>}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((a) => (
            <Card key={a.id} className="flex h-full flex-col">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-sm leading-snug">{a.name}</CardTitle>
                  <Badge variant={statusVariant(a.status)}>{a.status}</Badge>
                </div>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col">
                <p className="line-clamp-2 text-sm text-muted-foreground">
                  {a.description ?? a.spec?.description ?? "No description"}
                </p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {(a.spec?.agents ?? []).slice(0, 4).map((sa) => (
                    <Badge key={sa.id} variant="secondary">{sa.role}</Badge>
                  ))}
                </div>
                <div className="mt-auto flex gap-2 pt-4">
                  <Link href={`/agents/${a.id}/builder`} className="flex-1">
                    <Button variant="outline" size="sm" className="w-full">
                      <WorkflowIcon className="h-4 w-4" /> Builder
                    </Button>
                  </Link>
                  <Link href={`/agents/${a.id}/chat`} className="flex-1">
                    <Button size="sm" className="w-full">
                      <MessageSquare className="h-4 w-4" /> Chat
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
