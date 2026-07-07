"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Cake, Scissors, Sparkle, UtensilsCrossed, Dumbbell, Stethoscope, HeartPulse, Scale,
  Home, Car, Plane, Hotel, Store, ShoppingCart, GraduationCap, LayoutTemplate, Loader2, Wrench, Bot,
  type LucideIcon,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Client, Template } from "@/lib/types";
import { titleCase } from "@/lib/utils";
import { BUSINESS_TYPE_LABELS } from "@/lib/constants";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { CardGridSkeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toast";

const TEMPLATE_ICONS: Record<string, LucideIcon> = {
  bakery: Cake,
  barber: Scissors,
  salon: Sparkle,
  restaurant: UtensilsCrossed,
  gym: Dumbbell,
  dentist: Stethoscope,
  clinic: HeartPulse,
  lawyer: Scale,
  real_estate: Home,
  car_dealer: Car,
  travel_agency: Plane,
  hotel: Hotel,
  retail: Store,
  ecommerce: ShoppingCart,
  coaching_institute: GraduationCap,
};

export default function TemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[] | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [selected, setSelected] = useState<Template | null>(null);
  const [clientId, setClientId] = useState("");
  const [instantiating, setInstantiating] = useState(false);

  useEffect(() => {
    api.templates.list().then(setTemplates).catch(() => setTemplates([]));
    api.clients.list().then(setClients).catch(() => setClients([]));
  }, []);

  async function useTemplate() {
    if (!selected || !clientId) return;
    setInstantiating(true);
    try {
      const res = await api.templates.instantiate(selected.id, { client_id: clientId });
      toast("Template instantiated", "success");
      const projectId = res.project_id ?? res.project?.id;
      router.push(projectId ? `/projects/${projectId}` : "/projects");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Instantiation failed", "error");
      setInstantiating(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Templates"
        description="Pre-built agent teams for 15 business verticals. Instantiate one for a client in a single click."
      />

      {templates === null ? (
        <CardGridSkeleton count={9} />
      ) : templates.length === 0 ? (
        <EmptyState
          icon={LayoutTemplate}
          title="No templates available"
          description="The template library is served by the backend — make sure the AI engine has shipped its business templates."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {templates.map((t) => {
            const Icon = TEMPLATE_ICONS[t.business_type] ?? LayoutTemplate;
            const agentCount = t.agent_count ?? t.spec?.agents?.length ?? 0;
            const tools = (t.spec?.tools ?? []).slice(0, 4);
            return (
              <Card
                key={t.id}
                className="group flex h-full flex-col transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40"
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-violet-400/20 bg-gradient-to-br from-violet-500/20 to-indigo-500/10 text-violet-300 transition-transform duration-200 group-hover:scale-105">
                      <Icon className="h-5 w-5" />
                    </span>
                    <div>
                      <CardTitle className="text-sm">{t.name}</CardTitle>
                      <p className="text-xs text-muted-foreground">
                        {BUSINESS_TYPE_LABELS[t.business_type] ?? titleCase(t.business_type)}
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col">
                  <p className="line-clamp-2 text-sm text-muted-foreground">
                    {t.description ?? t.spec?.description ?? "Industry-tuned multi-agent team."}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1">
                    <Badge variant="muted"><Bot className="h-3 w-3" />{agentCount} agents</Badge>
                    {tools.map((tool) => (
                      <Badge key={tool.name} variant="secondary"><Wrench className="h-3 w-3" />{tool.name}</Badge>
                    ))}
                  </div>
                  <div className="mt-auto pt-4">
                    <Button
                      className="w-full"
                      variant="secondary"
                      onClick={() => {
                        setSelected(t);
                        setClientId(clients[0]?.id ?? "");
                      }}
                    >
                      Use template
                    </Button>
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
            <DialogTitle>Use “{selected?.name}”</DialogTitle>
          </DialogHeader>
          {clients.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              You need at least one client before instantiating a template. Add one on the Clients page.
            </p>
          ) : (
            <div className="space-y-1.5">
              <Label htmlFor="tpl-client">Instantiate for client</Label>
              <Select id="tpl-client" value={clientId} onChange={(e) => setClientId(e.target.value)}>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </Select>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelected(null)}>Cancel</Button>
            <Button onClick={useTemplate} disabled={instantiating || !clientId}>
              {instantiating ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Create project
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
