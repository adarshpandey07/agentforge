import type { Metadata } from "next";
import "@xyflow/react/dist/style.css";
import "./globals.css";
import { Toaster } from "@/components/ui/toast";

export const metadata: Metadata = {
  title: "AgentForge — Agent-as-a-Service",
  description:
    "Generate, customize and deploy production AI agents for any business.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
