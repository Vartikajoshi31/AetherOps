"use client";

import { useState, useEffect } from "react";
import {
  ShieldCheck,
  Terminal,
  Cpu,
  Layers,
  CheckCircle2,
  AlertCircle,
  Play,
  RefreshCw,
  Clock,
  Code2,
  Lock,
  FileCheck
} from "lucide-react";
import { api } from "@/lib/api";

const DEMO_TESTS = [
  {
    service: "checkout-service",
    file: "checkout-service/db.py",
    patch: "--- a/checkout-service/db.py\n+++ b/checkout-service/db.py\n@@ -32,3 +32,5 @@\n+    conn.in_use = True\n",
    test: "from db import DatabaseConnectionPool\nimport pytest\n\n@pytest.mark.asyncio\nasync def test_pool_connection_release():\n    pool = DatabaseConnectionPool(max_size=2)\n    conn = await pool.acquire()\n    await pool.release(conn)\n    assert len(pool._available) == 2\n"
  },
  {
    service: "payment-service",
    file: "payment-service/client.py",
    patch: "--- a/payment-service/client.py\n+++ b/payment-service/client.py\n@@ -20,2 +20,4 @@\n+        import random\n+        return self.base_backoff * (2 ** attempt) + random.uniform(0.1, 0.5)\n",
    test: "from client import PaymentGatewayClient\n\ndef test_jittered_delays():\n    client = PaymentGatewayClient(base_backoff=1.0, use_jitter=True)\n    delays = [client.calculate_retry_delay(2) for _ in range(10)]\n    assert len(set(delays)) > 5\n"
  },
  {
    service: "order-service",
    file: "order-service/shipping.py",
    patch: "--- a/order-service/shipping.py\n+++ b/order-service/shipping.py\n@@ -12,2 +12,4 @@\n+    if not order.shipping_address:\n+        return 0.0\n",
    test: "from shipping import Order, calculate_shipping_cost\n\ndef test_digital_order():\n    order = Order(id='d-1', is_digital=True, shipping_address=None)\n    assert calculate_shipping_cost(order) == 0.0\n"
  }
];

export default function SandboxPage() {
  const [selectedCase, setSelectedCase] = useState(DEMO_TESTS[0]);
  const [testCode, setTestCode] = useState(DEMO_TESTS[0].test);
  const [patchDiff, setPatchDiff] = useState(DEMO_TESTS[0].patch);
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState<any>(null);
  const [sandboxStatus, setSandboxStatus] = useState<any>(null);

  useEffect(() => {
    api.getSandboxStatus()
      .then(setSandboxStatus)
      .catch((err) => console.warn("Sandbox status offline:", err));
  }, []);

  const handleRunSandbox = async () => {
    setIsRunning(true);
    setOutput(null);

    try {
      const res = await api.validateSandboxPatch({
        service_name: selectedCase.service,
        affected_file: selectedCase.file,
        diff_patch: patchDiff,
        regression_test_code: testCode,
      });
      setOutput(res);
    } catch (e: any) {
      setOutput({
        success: false,
        syntax_valid: false,
        exit_code: 1,
        duration_seconds: 0.1,
        stdout: "",
        stderr: e.message || "Failed to execute in sandbox",
      });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/60 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Isolated Patch Validation Sandbox
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
              Zero Host Mutation
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Validates generated unified diff patches and executes regression tests inside temporary isolated workspaces before human sign-off.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono bg-card border border-border px-3.5 py-2 rounded-lg">
          <Lock className="h-3.5 w-3.5 text-emerald-400" />
          <span className="text-muted-foreground">Security Policy: </span>
          <span className="text-emerald-400 font-semibold">Strict TempFS Subprocess</span>
        </div>
      </div>

      {/* Security Guardrails Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-card border border-border shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs">Filesystem Isolation</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-sm font-bold text-foreground">Disposable Tempfs</div>
          <p className="text-[11px] text-muted-foreground">
            Code runs in ephemeral directories; auto-cleaned on completion.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs">AST Syntax Gate</span>
            <FileCheck className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-sm font-bold text-foreground">Python ast.parse()</div>
          <p className="text-[11px] text-muted-foreground">
            Guarantees zero syntax errors or invalid tokens before execution.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs">Execution Ceiling</span>
            <Clock className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-sm font-bold text-foreground">30-Second Hard Timeout</div>
          <p className="text-[11px] text-muted-foreground">
            Prevents infinite retry loops or hung socket connections.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs">Production Gate</span>
            <ShieldCheck className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-sm font-bold text-foreground">Enforced Human Gate</div>
          <p className="text-[11px] text-muted-foreground">
            System NEVER automatically deploys code to production.
          </p>
        </div>
      </div>

      {/* Interactive Sandbox Test Runner */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Preset Test Selection */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-2 border-b border-border/60 pb-3">
              <Terminal className="h-4 w-4 text-primary" />
              Target Microservice Test
            </h2>

            <div className="space-y-2">
              {DEMO_TESTS.map((c) => {
                const isSelected = selectedCase.service === c.service;
                return (
                  <button
                    key={c.service}
                    onClick={() => {
                      setSelectedCase(c);
                      setTestCode(c.test);
                      setPatchDiff(c.patch);
                    }}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      isSelected
                        ? "bg-secondary/70 border-primary text-foreground shadow-sm"
                        : "bg-card/40 border-border text-muted-foreground hover:bg-card hover:text-foreground"
                    }`}
                  >
                    <div className="font-semibold text-xs text-foreground font-mono">{c.service}</div>
                    <div className="text-[11px] text-muted-foreground font-mono mt-0.5">{c.file}</div>
                  </button>
                );
              })}
            </div>

            <button
              onClick={handleRunSandbox}
              disabled={isRunning}
              className="w-full py-2.5 px-4 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              {isRunning ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  Running Sandboxed Pytest...
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5" />
                  Execute Sandboxed Validation
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Columns: Editor & Execution Terminal Output */}
        <div className="lg:col-span-2 space-y-4">
          {/* Patch Diff Viewer */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-2">
            <div className="flex items-center justify-between text-xs text-muted-foreground pb-2 border-b border-border/60">
              <span className="font-mono text-foreground font-semibold">Candidate Patch Diff</span>
              <span className="font-mono">{selectedCase.file}</span>
            </div>
            <textarea
              value={patchDiff}
              onChange={(e) => setPatchDiff(e.target.value)}
              rows={4}
              className="w-full bg-black/40 border border-input rounded-lg p-3 text-xs font-mono text-zinc-300 resize-none focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Test Code */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-2">
            <div className="flex items-center justify-between text-xs text-muted-foreground pb-2 border-b border-border/60">
              <span className="font-mono text-foreground font-semibold">Regression Test Suite</span>
              <span className="font-mono text-cyan-400">pytest</span>
            </div>
            <textarea
              value={testCode}
              onChange={(e) => setTestCode(e.target.value)}
              rows={6}
              className="w-full bg-black/40 border border-input rounded-lg p-3 text-xs font-mono text-zinc-300 resize-none focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Terminal Output */}
          {output && (
            <div className="bg-black/60 border border-border rounded-xl p-5 shadow-sm space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <div className="flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-emerald-400" />
                  <span className="text-foreground font-semibold">Pytest Sandbox Console Output</span>
                </div>
                <div className="flex items-center gap-3 text-[11px]">
                  <span className="text-muted-foreground">Exit code: {output.exit_code}</span>
                  <span className="text-cyan-400">{output.duration_seconds}s</span>
                  {output.success ? (
                    <span className="text-emerald-400 font-bold">ALL TESTS PASSED</span>
                  ) : (
                    <span className="text-rose-400 font-bold">FAILED</span>
                  )}
                </div>
              </div>

              <pre className="text-zinc-300 text-[11px] whitespace-pre-wrap overflow-x-auto leading-relaxed">
                {output.stdout || output.stderr}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
