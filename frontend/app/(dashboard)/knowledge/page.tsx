"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BookOpen, FileUp, Globe, HelpCircle, Loader2, Plus, Database } from "lucide-react";
import { api } from "@/lib/api";
import type { KbDocument, KnowledgeBase } from "@/lib/types";
import { cn, formatDate, titleCase } from "@/lib/utils";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Badge, statusVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TableSkeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/toast";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function KnowledgePage() {
  const [bases, setBases] = useState<KnowledgeBase[] | null>(null);
  const [selected, setSelected] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<KbDocument[] | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [kbName, setKbName] = useState("");
  const [url, setUrl] = useState("");
  const [faq, setFaq] = useState("");
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const loadBases = useCallback(() => {
    api.knowledge.list().then(setBases).catch(() => setBases([]));
  }, []);

  useEffect(loadBases, [loadBases]);

  const loadDocs = useCallback((kb: KnowledgeBase) => {
    setDocuments(null);
    api.knowledge.listDocuments(kb.id).then(setDocuments).catch(() => setDocuments([]));
  }, []);

  function select(kb: KnowledgeBase) {
    setSelected(kb);
    loadDocs(kb);
  }

  async function createKb(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const kb = await api.knowledge.create({ name: kbName, vector_store: "pgvector", embedding_model: "text-embedding-3-small" });
      toast("Knowledge base created", "success");
      setCreateOpen(false);
      setKbName("");
      loadBases();
      select(kb);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Create failed", "error");
    } finally {
      setBusy(false);
    }
  }

  async function uploadFile(file: File) {
    if (!selected) return;
    setBusy(true);
    try {
      await api.knowledge.uploadFile(selected.id, file);
      toast(`Uploaded ${file.name}`, "success");
      loadDocs(selected);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Upload failed", "error");
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function addUrl() {
    if (!selected || !url.trim()) return;
    setBusy(true);
    try {
      await api.knowledge.addSource(selected.id, { source_type: "url", content: url.trim(), name: url.trim() });
      toast("URL queued for ingestion", "success");
      setUrl("");
      loadDocs(selected);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to add URL", "error");
    } finally {
      setBusy(false);
    }
  }

  async function addFaq() {
    if (!selected || !faq.trim()) return;
    setBusy(true);
    try {
      await api.knowledge.addSource(selected.id, { source_type: "faq", content: faq.trim(), name: "FAQ" });
      toast("FAQ ingested", "success");
      setFaq("");
      loadDocs(selected);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to add FAQ", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Knowledge"
        description="Ground your agents with business documents, websites and FAQs."
        actions={<Button onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" /> New knowledge base</Button>}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[300px,1fr]">
        <div className="space-y-2">
          {bases === null ? (
            <TableSkeleton rows={4} />
          ) : bases.length === 0 ? (
            <EmptyState
              icon={BookOpen}
              title="No knowledge bases"
              description="Create one, then upload PDFs, websites or FAQs."
              action={<Button size="sm" onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" /> Create</Button>}
            />
          ) : (
            bases.map((kb) => (
              <button
                key={kb.id}
                onClick={() => select(kb)}
                className={cn(
                  "w-full rounded-lg border bg-card p-3 text-left transition-colors hover:border-primary/50",
                  selected?.id === kb.id && "border-primary/70 bg-primary/5"
                )}
              >
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-primary" />
                  <p className="text-sm font-medium">{kb.name}</p>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {kb.vector_store ?? "pgvector"} · {kb.embedding_model ?? "default embeddings"}
                </p>
              </button>
            ))
          )}
        </div>

        <div>
          {!selected ? (
            <EmptyState icon={BookOpen} title="Select a knowledge base" description="Choose a KB to upload sources and track indexing status." />
          ) : (
            <div className="space-y-5">
              <Tabs defaultValue="file">
                <TabsList>
                  <TabsTrigger value="file"><FileUp className="mr-1.5 h-3.5 w-3.5" />File</TabsTrigger>
                  <TabsTrigger value="url"><Globe className="mr-1.5 h-3.5 w-3.5" />URL</TabsTrigger>
                  <TabsTrigger value="faq"><HelpCircle className="mr-1.5 h-3.5 w-3.5" />FAQ</TabsTrigger>
                </TabsList>
                <TabsContent value="file">
                  <div className="rounded-lg border border-dashed p-6 text-center">
                    <p className="mb-3 text-sm text-muted-foreground">Upload PDF, DOCX, CSV or XLSX documents.</p>
                    <input
                      ref={fileRef}
                      type="file"
                      accept=".pdf,.docx,.csv,.xlsx,.txt,.md"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) void uploadFile(f);
                      }}
                    />
                    <Button variant="secondary" onClick={() => fileRef.current?.click()} disabled={busy}>
                      {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
                      Choose file
                    </Button>
                  </div>
                </TabsContent>
                <TabsContent value="url">
                  <div className="flex gap-2">
                    <Input placeholder="https://client-website.com/menu" value={url} onChange={(e) => setUrl(e.target.value)} />
                    <Button onClick={addUrl} disabled={busy || !url.trim()}>
                      {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Globe className="h-4 w-4" />}
                      Ingest
                    </Button>
                  </div>
                </TabsContent>
                <TabsContent value="faq">
                  <div className="space-y-2">
                    <Textarea
                      rows={5}
                      placeholder={"Q: What are your opening hours?\nA: Mon–Sat, 8am–6pm.\n\nQ: Do you deliver?\nA: Yes, within 10km."}
                      value={faq}
                      onChange={(e) => setFaq(e.target.value)}
                    />
                    <Button onClick={addFaq} disabled={busy || !faq.trim()}>
                      {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <HelpCircle className="h-4 w-4" />}
                      Add FAQ
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>

              <div>
                <h3 className="mb-2 text-sm font-semibold text-muted-foreground">Documents</h3>
                {documents === null ? (
                  <TableSkeleton rows={3} />
                ) : documents.length === 0 ? (
                  <EmptyState icon={FileUp} title="No documents yet" description="Upload a file or ingest a URL above." />
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Source</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Added</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {documents.map((d) => (
                        <TableRow key={d.id}>
                          <TableCell className="font-medium">{d.name ?? "Untitled"}</TableCell>
                          <TableCell><Badge variant="secondary">{titleCase(d.source_type)}</Badge></TableCell>
                          <TableCell><Badge variant={statusVariant(d.status)}>{d.status}</Badge></TableCell>
                          <TableCell className="text-right text-muted-foreground">{formatDate(d.created_at)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>New knowledge base</DialogTitle></DialogHeader>
          <form onSubmit={createKb} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="kb-name">Name</Label>
              <Input id="kb-name" required placeholder="Bakery menu & policies" value={kbName} onChange={(e) => setKbName(e.target.value)} />
            </div>
            <p className="text-xs text-muted-foreground">Vector store: pgvector · Embeddings: text-embedding-3-small</p>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={busy}>Create</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
