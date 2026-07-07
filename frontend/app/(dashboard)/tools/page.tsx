"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Mail, Calendar, MapPin, MessageCircle, Hash, Phone, CreditCard, ShoppingBag, Megaphone,
  Cloud, Zap, GitFork, Braces, Webhook, Database, CheckCircle2, Loader2, Wrench,
  type LucideIcon,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Tool } from "@/lib/types";
import { INTEGRATION_CATALOG, type IntegrationDef } from "@/lib/constants";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CardGridSkeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toast";

const PROVIDER_ICONS: Record<string, LucideIcon> = {
  gmail: Mail,
  google_calendar: Calendar,
  google_maps: MapPin,
  whatsapp: MessageCircle,
  slack: Hash,
  twilio: Phone,
  stripe: CreditCard,
  shopify: ShoppingBag,
  hubspot: Megaphone,
  salesforce: Cloud,
  zapier: Zap,
  n8n: GitFork,
  custom_api: Braces,
  webhook: Webhook,
  database: Database,
};

export default function ToolsPage() {
  const [connected, setConnected] = useState<Tool[] | null>(null);
  const [selected, setSelected] = useState<IntegrationDef | null>(null);
  const [config, setConfig] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.tools.list().then(setConnected).catch(() => setConnected([]));
  }, []);

  useEffect(load, [load]);

  function connectedTool(provider: string): Tool | undefined {
    return connected?.find((t) => t.provider === provider || t.name === provider);
  }

  function openConnect(def: IntegrationDef) {
    setSelected(def);
    setConfig({});
  }

  async function connect(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setBusy(true);
    try {
      await api.tools.create({
        name: selected.provider,
        type: selected.type,
        provider: selected.provider,
        config,
      });
      toast(`${selected.name} connected`, "success");
      setSelected(null);
      load();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Connection failed", "error");
    } finally {
      setBusy(false);
    }
  }

  async function disconnect(tool: Tool) {
    try {
      await api.tools.remove(tool.id);
      toast("Disconnected", "success");
      load();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to disconnect", "error");
    }
  }

  return (
    <div>
      <PageHeader
        title="Tools & integrations"
        description="Connect the services your agents can act through. Credentials are stored encrypted per tenant."
      />

      {connected === null ? (
        <CardGridSkeleton count={9} />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {INTEGRATION_CATALOG.map((def) => {
            const Icon = PROVIDER_ICONS[def.provider] ?? Wrench;
            const existing = connectedTool(def.provider);
            return (
              <Card key={def.provider} className="flex h-full flex-col transition-colors hover:border-primary/40">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary">
                        <Icon className="h-5 w-5 text-foreground" />
                      </span>
                      <div>
                        <CardTitle className="text-sm">{def.name}</CardTitle>
                        <p className="text-xs text-muted-foreground">{def.category}</p>
                      </div>
                    </div>
                    {existing ? (
                      <Badge variant="success"><CheckCircle2 className="h-3 w-3" /> Connected</Badge>
                    ) : null}
                  </div>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col">
                  <p className="text-sm text-muted-foreground">{def.description}</p>
                  <div className="mt-auto pt-4">
                    {existing ? (
                      <Button variant="outline" size="sm" className="w-full" onClick={() => void disconnect(existing)}>
                        Disconnect
                      </Button>
                    ) : (
                      <Button variant="secondary" size="sm" className="w-full" onClick={() => openConnect(def)}>
                        Connect
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Dialog open={selected !== null} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Connect {selected?.name}</DialogTitle>
          </DialogHeader>
          <form onSubmit={connect} className="space-y-4">
            {selected?.fields.map((f) => (
              <div key={f.key} className="space-y-1.5">
                <Label htmlFor={`cfg-${f.key}`}>{f.label}</Label>
                <Input
                  id={`cfg-${f.key}`}
                  type={f.secret ? "password" : "text"}
                  placeholder={f.placeholder}
                  required
                  value={config[f.key] ?? ""}
                  onChange={(e) => setConfig({ ...config, [f.key]: e.target.value })}
                />
              </div>
            ))}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setSelected(null)}>Cancel</Button>
              <Button type="submit" disabled={busy}>
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Connect
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
