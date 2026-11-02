"use client";

import { useState } from "react";
import {
  Settings,
  Key,
  Cpu,
  Database,
  Shield,
  GitBranch,
  Save,
  CheckCircle2,
  Lock,
  Eye,
  EyeOff,
  Server,
  Terminal,
  Layers,
  Sparkles
} from "lucide-react";

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [selectedModel, setSelectedModel] = useState("gpt-4o");
  const [temperature, setTemperature] = useState(0.1);
  const [maxRetries, setMaxRetries] = useState(2);
  const [tokenBudget, setTokenBudget] = useState(50000);

  // Sandbox settings
  const [sandboxTimeout, setSandboxTimeout] = useState(30);
  const [sandboxMemory, setSandboxMemory] = useState(512);
  const [enableDocker, setEnableDocker] = useState(false);

  // GitHub integration
  const [githubToken, setGithubToken] = useState("");
  const [githubOrg, setGithubOrg] = useState("acme");
  const [autoCreatePR, setAutoCreatePR] = useState(true);

  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/60 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Platform Settings & AI Configuration
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-medium">
              Enterprise Ready
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Configure multi-agent LLM inference, vector database connectivity, sandboxed test execution parameters, and GitHub credentials.
          </p>
        </div>

        {savedSuccess && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-medium">
            <CheckCircle2 className="h-4 w-4" />
            <span>Settings saved successfully</span>
          </div>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-8">
        {/* LLM & Multi-Agent Swarm Settings */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-5">
          <div className="flex items-center gap-2 border-b border-border/60 pb-3">
            <Cpu className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold text-foreground">
              LLM Inference & Agent Orchestration
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground flex items-center justify-between">
                <span>OpenAI API Key (Optional)</span>
                <span className="text-[11px] text-muted-foreground">Zero-config local fallback active</span>
              </label>
              <div className="relative">
                <input
                  type={showApiKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-proj-..."
                  className="w-full bg-background border border-input rounded-lg pl-3 pr-10 py-2 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground"
                >
                  {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Leave blank to run deterministic expert heuristic reasoning for offline/zero-cost testing.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">
                Primary Reasoning Model
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-background border border-input rounded-lg px-3 py-2 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="gpt-4o">gpt-4o (State of the art root cause analysis & code generation)</option>
                <option value="gpt-4o-mini">gpt-4o-mini (Faster, cost-optimized agent execution)</option>
                <option value="local-heuristics">local-deterministic (Offline rule engine)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-foreground">
                <span>Temperature (Sampling Variability)</span>
                <span className="font-mono text-cyan-400 font-semibold">{temperature}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full accent-primary"
              />
              <p className="text-[11px] text-muted-foreground">
                Low temperature (0.05-0.15) produces deterministic, minimal diffs and structured Pydantic outputs.
              </p>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-foreground">
                <span>Max Patch Validation Retries</span>
                <span className="font-mono text-purple-400 font-semibold">{maxRetries} attempts</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                value={maxRetries}
                onChange={(e) => setMaxRetries(Number(e.target.value))}
                className="w-full accent-primary"
              />
              <p className="text-[11px] text-muted-foreground">
                Maximum self-healing attempts if sandboxed test validation detects a regression.
              </p>
            </div>
          </div>
        </div>

        {/* Sandboxed Execution & Security Settings */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-5">
          <div className="flex items-center gap-2 border-b border-border/60 pb-3">
            <Shield className="h-4 w-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-foreground">
              Patch Sandbox & Security Isolation
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">
                Execution Timeout (Seconds)
              </label>
              <input
                type="number"
                min="5"
                max="120"
                value={sandboxTimeout}
                onChange={(e) => setSandboxTimeout(Number(e.target.value))}
                className="w-full bg-background border border-input rounded-lg px-3 py-2 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <p className="text-[11px] text-muted-foreground">
                Kills hung tests or infinite loops in sandboxed patch verification.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">
                Memory Ceiling (MB)
              </label>
              <input
                type="number"
                min="128"
                max="2048"
                step="128"
                value={sandboxMemory}
                onChange={(e) => setSandboxMemory(Number(e.target.value))}
                className="w-full bg-background border border-input rounded-lg px-3 py-2 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <p className="text-[11px] text-muted-foreground">
                Maximum RSS memory allowed per sandbox execution before SIGKILL.
              </p>
            </div>

            <div className="md:col-span-2 p-4 rounded-xl bg-secondary/30 border border-border flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-foreground block">
                  Enforce Docker Container Sandbox Isolation
                </span>
                <span className="text-[11px] text-muted-foreground">
                  When enabled, uses disposable non-privileged Docker containers instead of local isolated tempfs.
                </span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableDocker}
                  onChange={(e) => setEnableDocker(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
          </div>
        </div>

        {/* GitHub Repository & PR Integration */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-5">
          <div className="flex items-center gap-2 border-b border-border/60 pb-3">
            <GitBranch className="h-4 w-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-foreground">
              GitHub Pull Request & Approval Automation
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">
                GitHub Personal Access Token (PAT)
              </label>
              <input
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxx"
                className="w-full bg-background border border-input rounded-lg px-3 py-2 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">
                GitHub Organization / Owner
              </label>
              <input
                type="text"
                value={githubOrg}
                onChange={(e) => setGithubOrg(e.target.value)}
                placeholder="acme"
                className="w-full bg-background border border-input rounded-lg px-3 py-2 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="md:col-span-2 p-4 rounded-xl bg-secondary/30 border border-border flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-foreground block">
                  Automatic PR Draft Creation Upon Human Approval
                </span>
                <span className="text-[11px] text-muted-foreground">
                  Creates an atomic pull request with verified patch diff and regression test upon human sign-off.
                </span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoCreatePR}
                  onChange={(e) => setAutoCreatePR(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Submit Bar */}
        <div className="flex items-center justify-end gap-4 pt-2">
          <button
            type="submit"
            className="py-2.5 px-6 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-xs flex items-center gap-2 transition-colors shadow-sm"
          >
            <Save className="h-4 w-4" />
            Save Configuration Changes
          </button>
        </div>
      </form>
    </div>
  );
}
