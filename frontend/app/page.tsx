"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Bot, Sparkles, Workflow, Rocket } from "lucide-react";
import { getToken } from "@/lib/auth";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    if (getToken()) router.replace("/dashboard");
  }, [router]);

  return (
    <div className="bg-spotlight relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6">
      <div className="bg-grid pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_70%_60%_at_50%_30%,black,transparent)]" />

      <div className="relative flex max-w-2xl flex-col items-center text-center">
        <div className="animate-fade-up mb-8 flex items-center gap-2.5">
          <div className="gradient-brand flex h-9 w-9 items-center justify-center rounded-xl shadow-glow">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <span className="text-base font-semibold tracking-tight">
            Agent<span className="gradient-text">Forge</span>
          </span>
        </div>

        <div className="animate-fade-up mb-6 inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-3.5 py-1.5 text-xs text-muted-foreground [animation-delay:80ms]">
          <Sparkles className="h-3 w-3 text-violet-400" />
          AI agent teams, generated in seconds
        </div>

        <h1 className="animate-fade-up text-5xl font-semibold leading-[1.08] tracking-tighter sm:text-6xl [animation-delay:140ms]">
          The Shopify of
          <br />
          <span className="gradient-text">AI Agents</span>
        </h1>

        <p className="animate-fade-up mt-6 max-w-md text-base leading-relaxed text-muted-foreground [animation-delay:220ms]">
          Describe any business and get a production-ready team of AI agents —
          with tools, knowledge, and workflows — deployed for your clients.
        </p>

        <div className="animate-fade-up mt-9 flex items-center gap-3 [animation-delay:300ms]">
          <Link
            href="/login"
            className="gradient-brand group inline-flex h-11 items-center gap-2 rounded-lg px-6 text-sm font-medium text-white shadow-glow transition-all duration-150 hover:brightness-110 active:scale-[0.98]"
          >
            Get started
            <ArrowRight className="h-4 w-4 transition-transform duration-150 group-hover:translate-x-0.5" />
          </Link>
          <Link
            href="/register"
            className="inline-flex h-11 items-center rounded-lg border border-white/[0.08] bg-white/[0.03] px-6 text-sm font-medium text-foreground transition-colors duration-150 hover:bg-white/[0.06]"
          >
            Create account
          </Link>
        </div>

        <div className="animate-fade-up mt-14 grid grid-cols-3 gap-6 text-left [animation-delay:380ms]">
          {[
            { icon: Sparkles, title: "Generate", desc: "Agent teams from a prompt" },
            { icon: Workflow, title: "Orchestrate", desc: "Visual workflow builder" },
            { icon: Rocket, title: "Deploy", desc: "One-click client portals" },
          ].map((f) => (
            <div key={f.title} className="flex flex-col gap-1.5">
              <f.icon className="h-4 w-4 text-violet-400" />
              <p className="text-sm font-medium">{f.title}</p>
              <p className="text-xs text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
