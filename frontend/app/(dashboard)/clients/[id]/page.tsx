"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, FolderKanban, Mail, Phone, Building2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Client, Project } from "@/lib/types";
import { formatDate, titleCase } from "@/lib/utils";
import { BUSINESS_TYPE_LABELS } from "@/lib/constants";
import { EmptyState } from "@/components/empty-state";
import { Badge, statusVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton, CardGridSkeleton } from "@/components/ui/skeleton";

export default function ClientDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [client, setClient] = useState<Client | null>(null);
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.clients.get(id).then(setClient).catch((e: Error) => setError(e.message));
    api.projects
      .list({ client_id: id })
      .then((all) => setProjects(all.filter((p) => p.client_id === id || !p.client_id)))
      .catch(() => setProjects([]));
  }, [id]);

  if (error) {
    return <p className="text-sm text-red-400">Failed to load client: {error}</p>;
  }

  return (
    <div>
      <Link href="/clients" className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to clients
      </Link>

      {client === null ? (
        <div className="space-y-4">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : (
        <>
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-xl font-semibold tracking-tight">{client.name}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                {client.business_type ? (
                  <Badge variant="secondary">
                    {BUSINESS_TYPE_LABELS[client.business_type] ?? titleCase(client.business_type)}
                  </Badge>
                ) : null}
                {client.email ? (
                  <span className="inline-flex items-center gap-1.5"><Mail className="h-3.5 w-3.5" />{client.email}</span>
                ) : null}
                {client.phone ? (
                  <span className="inline-flex items-center gap-1.5"><Phone className="h-3.5 w-3.5" />{client.phone}</span>
                ) : null}
                {client.company ? (
                  <span className="inline-flex items-center gap-1.5"><Building2 className="h-3.5 w-3.5" />{client.company}</span>
                ) : null}
              </div>
            </div>
            <Link href="/generate">
              <Button>New agent for this client</Button>
            </Link>
          </div>

          {client.notes ? (
            <Card className="mb-6">
              <CardHeader className="pb-2"><CardTitle className="text-sm">Notes</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-muted-foreground">{client.notes}</p></CardContent>
            </Card>
          ) : null}
        </>
      )}

      <h2 className="mb-3 text-sm font-semibold text-muted-foreground">Projects</h2>
      {projects === null ? (
        <CardGridSkeleton count={3} />
      ) : projects.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title="No projects yet"
          description="Generate an agent or instantiate a template for this client."
          action={<Link href="/templates"><Button variant="secondary" size="sm">Browse templates</Button></Link>}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`}>
              <Card className="h-full transition-colors hover:border-primary/50">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">{p.name}</CardTitle>
                    <Badge variant={statusVariant(p.status)}>{p.status}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="line-clamp-2 text-sm text-muted-foreground">{p.description ?? "No description"}</p>
                  <p className="mt-3 text-xs text-muted-foreground">
                    {p.agent_count ?? 0} agent{(p.agent_count ?? 0) === 1 ? "" : "s"} · {formatDate(p.created_at)}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
