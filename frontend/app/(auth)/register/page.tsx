"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { setToken, cacheUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function RegisterPage() {
  const router = useRouter();
  const [tenantName, setTenantName] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.auth.register({
        email,
        password,
        full_name: fullName,
        tenant_name: tenantName,
      });
      if (res.access_token) {
        setToken(res.access_token);
        if (res.user) cacheUser(res.user);
        router.replace("/dashboard");
      } else {
        // Some backends return the user only; log in explicitly.
        const login = await api.auth.login({ email, password });
        setToken(login.access_token);
        router.replace("/dashboard");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed");
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create your workspace</CardTitle>
        <CardDescription>Start building AI agents for your clients</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="tenant">Agency name</Label>
            <Input
              id="tenant"
              required
              placeholder="Acme Automation"
              value={tenantName}
              onChange={(e) => setTenantName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="name">Your name</Label>
            <Input
              id="name"
              required
              placeholder="Jane Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              required
              autoComplete="email"
              placeholder="you@agency.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error ? <p className="text-sm text-red-400">{error}</p> : null}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Create workspace
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
