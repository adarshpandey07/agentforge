"use client";

import { useCallback, useEffect, useState } from "react";
import { Copy, KeyRound, Loader2, Plus, Trash2, Users } from "lucide-react";
import { api } from "@/lib/api";
import type { ApiKey } from "@/lib/types";
import { useAuth } from "@/lib/auth";
import { formatDate } from "@/lib/utils";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TableSkeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toast";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function SettingsPage() {
  const { user } = useAuth({ guard: false });
  const [keys, setKeys] = useState<ApiKey[] | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [keyName, setKeyName] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.apiKeys.list().then(setKeys).catch(() => setKeys([]));
  }, []);

  useEffect(load, [load]);

  async function createKey(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const created = await api.apiKeys.create({ name: keyName });
      setNewKey(created.key ?? null);
      setKeyName("");
      load();
      if (!created.key) {
        toast("API key created", "success");
        setCreateOpen(false);
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to create key", "error");
    } finally {
      setBusy(false);
    }
  }

  async function revoke(k: ApiKey) {
    try {
      await api.apiKeys.revoke(k.id);
      toast("Key revoked", "success");
      load();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Revoke failed", "error");
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title="Settings" description="Workspace configuration, API access and team." />

      <Tabs defaultValue="api-keys">
        <TabsList>
          <TabsTrigger value="api-keys">API keys</TabsTrigger>
          <TabsTrigger value="team">Team</TabsTrigger>
          <TabsTrigger value="tenant">Workspace</TabsTrigger>
        </TabsList>

        <TabsContent value="api-keys">
          <div className="mb-4 flex justify-end">
            <Button size="sm" onClick={() => { setNewKey(null); setCreateOpen(true); }}>
              <Plus className="h-4 w-4" /> Create key
            </Button>
          </div>
          {keys === null ? (
            <TableSkeleton rows={3} />
          ) : keys.length === 0 ? (
            <EmptyState
              icon={KeyRound}
              title="No API keys"
              description="Create a key to call the AgentForge API from client apps and webhooks."
              action={<Button size="sm" onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" /> Create key</Button>}
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Key</TableHead>
                  <TableHead>Scopes</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {keys.map((k) => (
                  <TableRow key={k.id}>
                    <TableCell className="font-medium">{k.name ?? "Unnamed"}</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {k.prefix ? `${k.prefix}••••••••` : "••••••••"}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {(k.scopes ?? ["full"]).map((s) => (
                          <Badge key={s} variant="secondary">{s}</Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(k.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon" onClick={() => void revoke(k)} aria-label="Revoke">
                        <Trash2 className="h-4 w-4 text-red-400" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </TabsContent>

        <TabsContent value="team">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Team members</CardTitle>
              <CardDescription>Roles: owner, admin, member, viewer.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Member</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">{user?.full_name ?? "You"}</TableCell>
                    <TableCell className="text-muted-foreground">{user?.email ?? "—"}</TableCell>
                    <TableCell><Badge variant="success">{user?.role ?? "owner"}</Badge></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
              <div className="mt-4 rounded-lg border border-dashed p-4 text-center">
                <Users className="mx-auto mb-2 h-5 w-5 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  Invitations are sent by email. Ask your backend admin to enable SMTP to invite teammates.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tenant">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Workspace profile</CardTitle>
              <CardDescription>Details of your agency tenant.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <Label>Workspace name</Label>
                <Input value={user?.tenant_name ?? ""} readOnly placeholder="Workspace" />
              </div>
              <div className="space-y-1.5">
                <Label>Tenant ID</Label>
                <Input value={user?.tenant_id ?? ""} readOnly className="font-mono text-xs" />
              </div>
              <div className="space-y-1.5">
                <Label>API base URL</Label>
                <Input value={process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"} readOnly className="font-mono text-xs" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create API key</DialogTitle></DialogHeader>
          {newKey ? (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Copy this key now — it will not be shown again.
              </p>
              <div className="flex items-center gap-2">
                <Input readOnly value={newKey} className="font-mono text-xs" />
                <Button
                  variant="secondary"
                  size="icon"
                  onClick={() => {
                    void navigator.clipboard.writeText(newKey);
                    toast("Copied to clipboard", "success");
                  }}
                  aria-label="Copy"
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
              <DialogFooter>
                <Button onClick={() => setCreateOpen(false)}>Done</Button>
              </DialogFooter>
            </div>
          ) : (
            <form onSubmit={createKey} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="key-name">Key name</Label>
                <Input id="key-name" required placeholder="Production webhook" value={keyName} onChange={(e) => setKeyName(e.target.value)} />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={busy}>
                  {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
                  Create
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
