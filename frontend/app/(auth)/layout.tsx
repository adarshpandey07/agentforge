import { Bot } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-spotlight relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-4">
      <div className="bg-grid pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,black,transparent)]" />
      <div className="relative mb-8 flex items-center gap-3 animate-fade-up">
        <div className="gradient-brand flex h-11 w-11 items-center justify-center rounded-xl shadow-glow">
          <Bot className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-lg font-semibold leading-none tracking-tight">
            Agent<span className="gradient-text">Forge</span>
          </p>
          <p className="mt-1.5 text-xs text-muted-foreground">
            The Shopify of AI Agents
          </p>
        </div>
      </div>
      <div className="relative w-full max-w-sm animate-fade-up [animation-delay:100ms]">
        {children}
      </div>
    </div>
  );
}
