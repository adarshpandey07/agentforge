"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Search, Users, Pencil, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Client } from "@/lib/types";
import { formatDate, titleCase } from "@/lib/utils";
import { BUSINESS_TYPES, BUSINESS_TYPE_LABELS } from "@/lib/constants";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { TableSkeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toast";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const emptyForm = { name: "", email: "", phone: "", company: "", business_type: "", notes: "" };

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[] | null>(null);
  const [query, setQuery] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Client | null>(null);
  const [deleting, setDeleting] = useState<Client | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  const load = useCallback((q?: string) => {
    api.clients
      .list(q ? { q } : undefined)
      .then(setClients)
      .catch((e: Error) => {
        setClients([]);
        toast(e.message, "error");
      });
  }, []);

  useEffect(() => {
    const t = setTimeout(() => load(query || undefined), query ? 300 : 0);
    return () => clearTimeout(t);
  }, [query, load]);

  function openCreate() {
    setEditing(null);
    setForm(emptyForm);
    setDialogOpen(true);
  }

  function openEdit(c: Client) {
    setEditing(c);
    setForm({
      name: c.name,
      email: c.email ?? "",
      phone: c.phone ?? "",
      company: c.company ?? "",
      business_type: c.business_type ?? "",
      notes: c.notes ?? "",
    });
    setDialogOpen(true);
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const body = { ...form, business_type: form.business_type || undefined };
      if (editing) {
        await api.clients.update(editing.id, body);
        toast("Client updated", "success");
      } else {
        await api.clients.create(body);
        toast("Client created", "success");
      }
      setDialogOpen(false);
      load(query || undefined);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Save failed", "error");
    } finally {
      setSaving(false);
    }
  }

  async function confirmDelete() {
    if (!deleting) return;
    try {
      await api.clients.remove(deleting.id);
      toast("Client deleted", "success");
      setDeleting(null);
      load(query || undefined);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Delete failed", "error");
    }
  }

  return (
    <div>
      <PageHeader
        title="Clients"
        description="The businesses you build agents for."
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" /> Add client
          </Button>
        }
      />

      <div className="mb-4 relative max-w-sm">
        <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search clients…"
          className="pl-8"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {clients === null ? (
        <TableSkeleton rows={6} />
      ) : clients.length === 0 ? (
        <EmptyState
          icon={Users}
          title={query ? "No clients match your search" : "No clients yet"}
          description={query ? "Try a different search term." : "Add your first client to start building agents for them."}
          action={!query ? <Button size="sm" onClick={openCreate}><Plus className="h-4 w-4" /> Add client</Button> : undefined}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Business</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Added</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {clients.map((c) => (
              <TableRow key={c.id}>
                <TableCell>
                  <Link href={`/clients/${c.id}`} className="font-medium hover:text-primary hover:underline">
                    {c.name}
                  </Link>
                  {c.company ? <p className="text-xs text-muted-foreground">{c.company}</p> : null}
                </TableCell>
                <TableCell>
                  {c.business_type ? (
                    <Badge variant="secondary">{BUSINESS_TYPE_LABELS[c.business_type] ?? titleCase(c.business_type)}</Badge>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground">{c.email ?? "—"}</TableCell>
                <TableCell className="text-muted-foreground">{c.phone ?? "—"}</TableCell>
                <TableCell className="text-muted-foreground">{formatDate(c.created_at)}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button variant="ghost" size="icon" onClick={() => openEdit(c)} aria-label="Edit">
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => setDeleting(c)} aria-label="Delete">
                      <Trash2 className="h-4 w-4 text-red-400" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "Edit client" : "Add client"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={save} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="c-name">Name</Label>
              <Input id="c-name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="c-email">Email</Label>
                <Input id="c-email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="c-phone">Phone</Label>
                <Input id="c-phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="c-company">Company</Label>
                <Input id="c-company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="c-type">Business type</Label>
                <Select id="c-type" value={form.business_type} onChange={(e) => setForm({ ...form, business_type: e.target.value })}>
                  <option value="">Select…</option>
                  {BUSINESS_TYPES.map((t) => (
                    <option key={t} value={t}>{BUSINESS_TYPE_LABELS[t]}</option>
                  ))}
                </Select>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="c-notes">Notes</Label>
              <Textarea id="c-notes" rows={3} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={saving}>{editing ? "Save changes" : "Create client"}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={deleting !== null} onOpenChange={(o) => !o && setDeleting(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete client?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            This will permanently delete <span className="font-medium text-foreground">{deleting?.name}</span> and cannot be undone.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleting(null)}>Cancel</Button>
            <Button variant="destructive" onClick={confirmDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
