"use client";

import { useState, useEffect } from "react";
import {
  GitBranch,
  GitCommit,
  FolderGit2,
  FileCode,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  ChevronRight,
  ExternalLink,
  Cpu,
  Database,
  Code2
} from "lucide-react";
import { api } from "@/lib/api";

interface Repository {
  id: string;
  name: string;
  full_name: string;
  default_branch: string;
  clone_url?: string;
  local_path?: string;
  indexed_at?: string;
  index_status: string;
  total_files: number;
  created_at: string;
}

interface ServiceFile {
  name: string;
  path: string;
  type: "file" | "test";
  functions: string[];
  classes: string[];
  description: string;
}

const DEMO_SERVICES = [
  {
    id: "checkout-service",
    name: "Checkout Service",
    port: "8001",
    language: "Python 3.13 / FastAPI",
    description: "Cart checkout, payment coordination, and order finalizing",
    files: [
      {
        name: "db.py",
        path: "checkout-service/db.py",
        type: "file",
        classes: ["DatabaseConnectionPool", "MockConnection"],
        functions: ["acquire", "release", "get_pool_status"],
        description: "Connection pool manager with 10 max connections and leak vulnerability"
      },
      {
        name: "app.py",
        path: "checkout-service/app.py",
        type: "file",
        classes: ["CheckoutRequest", "CheckoutResponse"],
        functions: ["process_checkout", "health_check"],
        description: "FastAPI checkout endpoint with unhandled exception connection leak"
      },
      {
        name: "test_checkout.py",
        path: "checkout-service/tests/test_checkout.py",
        type: "test",
        classes: [],
        functions: ["test_connection_pool_acquire_and_release", "test_pool_exhaustion_scenario"],
        description: "Pytest unit tests verifying pool exhaustion and leak handling"
      }
    ] as ServiceFile[]
  },
  {
    id: "payment-service",
    name: "Payment Gateway Service",
    port: "8002",
    language: "Python 3.13 / AsyncIO",
    description: "Third-party payment gateway integration & tokenization",
    files: [
      {
        name: "client.py",
        path: "payment-service/client.py",
        type: "file",
        classes: ["PaymentGatewayClient", "PaymentException"],
        functions: ["charge", "calculate_retry_delay"],
        description: "Deterministic exponential backoff without jitter leading to thundering herd"
      },
      {
        name: "test_payment.py",
        path: "payment-service/tests/test_payment.py",
        type: "test",
        classes: [],
        functions: ["test_retry_delay_deterministic_vs_jitter", "test_retry_storm_prevention"],
        description: "Unit tests asserting decorrelated jittered backoff intervals"
      }
    ] as ServiceFile[]
  },
  {
    id: "inventory-service",
    name: "Inventory & Stock Service",
    port: "8003",
    language: "Python 3.13",
    description: "Warehouse stock reservation and low-latency SKU cache",
    files: [
      {
        name: "cache.py",
        path: "inventory-service/cache.py",
        type: "file",
        classes: ["InventoryCache"],
        functions: ["get", "set", "evict_expired", "size"],
        description: "Unbounded in-memory cache without max-size cap causing OOM leaks"
      },
      {
        name: "test_inventory.py",
        path: "inventory-service/tests/test_inventory.py",
        type: "test",
        classes: [],
        functions: ["test_inventory_cache_max_size_eviction", "test_ttl_expiry"],
        description: "Regression suite asserting LRU eviction under memory pressure"
      }
    ] as ServiceFile[]
  },
  {
    id: "order-service",
    name: "Order Processing Service",
    port: "8004",
    language: "Python 3.13 / Pydantic",
    description: "Order lifecycle, shipping fee calculations, and digital delivery",
    files: [
      {
        name: "shipping.py",
        path: "order-service/shipping.py",
        type: "file",
        classes: ["Order", "Address"],
        functions: ["calculate_shipping_cost"],
        description: "Null pointer / AttributeError when calculating shipping for digital orders"
      },
      {
        name: "test_shipping.py",
        path: "order-service/tests/test_shipping.py",
        type: "test",
        classes: [],
        functions: ["test_digital_order_no_shipping_address", "test_standard_order_shipping"],
        description: "Unit tests guarding against NoneType address dereference"
      }
    ] as ServiceFile[]
  }
];

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [selectedService, setSelectedService] = useState(DEMO_SERVICES[0]);
  const [selectedFile, setSelectedFile] = useState<ServiceFile>(DEMO_SERVICES[0].files[0]);
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexMessage, setIndexMessage] = useState<string | null>(null);

  useEffect(() => {
    loadRepositories();
  }, []);

  const loadRepositories = async () => {
    try {
      const data = await api.getRepositories();
      setRepos(data);
    } catch (e: any) {
      console.error("Failed to load repositories", e);
    }
  };

  const handleTriggerIndex = async (repoId: string) => {
    setIsIndexing(true);
    setIndexMessage(null);
    try {
      const res = await api.indexRepository(repoId);
      setIndexMessage(res.message);
      await loadRepositories();
    } catch (e: any) {
      setIndexMessage(`Indexing failed: ${e.message}`);
    } finally {
      setIsIndexing(false);
    }
  };

  const primaryRepo = repos[0];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/60 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Connected Repositories & AST Code Intelligence
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
              Synchronized
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Tree-sitter AST structural parsing, function extraction, and Qdrant vector indexing for automated root cause analysis.
          </p>
        </div>

        {primaryRepo && (
          <button
            onClick={() => handleTriggerIndex(primaryRepo.id)}
            disabled={isIndexing}
            className="py-2.5 px-4 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground font-medium text-xs flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isIndexing ? "animate-spin" : ""}`} />
            {isIndexing ? "Indexing Repository with Tree-sitter..." : "Trigger Full AST Re-Index"}
          </button>
        )}
      </div>

      {indexMessage && (
        <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span>{indexMessage}</span>
          </div>
          <button onClick={() => setIndexMessage(null)} className="text-muted-foreground hover:text-foreground">
            ✕
          </button>
        </div>
      )}

      {/* Connected Repository Card */}
      {primaryRepo && (
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                <FolderGit2 className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-foreground font-mono">
                  {primaryRepo.full_name}
                </h2>
                <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5 font-mono">
                  <span className="flex items-center gap-1">
                    <GitBranch className="h-3 w-3" /> {primaryRepo.default_branch}
                  </span>
                  <span>•</span>
                  <span>Path: {primaryRepo.local_path || "demo-services/"}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-6 text-xs font-mono">
              <div>
                <span className="text-muted-foreground block text-[10px] uppercase">Status</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1 mt-0.5">
                  <CheckCircle2 className="h-3 w-3" /> {primaryRepo.index_status}
                </span>
              </div>
              <div className="h-6 w-px bg-border" />
              <div>
                <span className="text-muted-foreground block text-[10px] uppercase">Files Tracked</span>
                <span className="text-foreground font-bold mt-0.5 block">{primaryRepo.total_files} files</span>
              </div>
              <div className="h-6 w-px bg-border" />
              <div>
                <span className="text-muted-foreground block text-[10px] uppercase">Last Indexed</span>
                <span className="text-zinc-400 mt-0.5 block">
                  {primaryRepo.indexed_at ? new Date(primaryRepo.indexed_at).toLocaleTimeString() : "Just now"}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Microservices Explorer & AST Symbol Browser */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" />
            Microservices Codebase & AST Symbol Browser
          </h2>
          <span className="text-xs text-muted-foreground">
            Isolated microservices powering autonomous chaos simulations
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Services Selector Column */}
          <div className="lg:col-span-1 space-y-2">
            {DEMO_SERVICES.map((service) => {
              const isSelected = selectedService.id === service.id;
              return (
                <button
                  key={service.id}
                  onClick={() => {
                    setSelectedService(service);
                    setSelectedFile(service.files[0]);
                  }}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                    isSelected
                      ? "bg-secondary/70 border-primary text-foreground shadow-sm"
                      : "bg-card/60 border-border text-muted-foreground hover:bg-card hover:text-foreground"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-foreground">{service.name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-background border border-border">
                      :{service.port}
                    </span>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-1 line-clamp-1">
                    {service.description}
                  </p>
                  <div className="mt-2 text-[10px] text-zinc-400 font-mono">
                    {service.files.length} indexed modules
                  </div>
                </button>
              );
            })}
          </div>

          {/* Files List in Selected Service */}
          <div className="lg:col-span-1 space-y-2">
            <div className="text-xs font-semibold text-muted-foreground px-1 pb-1 uppercase tracking-wider">
              {selectedService.name} Files
            </div>
            {selectedService.files.map((file) => {
              const isSelected = selectedFile.path === file.path;
              return (
                <button
                  key={file.path}
                  onClick={() => setSelectedFile(file)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    isSelected
                      ? "bg-primary/10 border-primary/40 text-foreground"
                      : "bg-card/40 border-border/60 text-muted-foreground hover:bg-card hover:text-foreground"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <FileCode className={`h-4 w-4 ${file.type === "test" ? "text-amber-400" : "text-cyan-400"}`} />
                    <span className="font-mono text-xs font-medium text-foreground">{file.name}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-1 line-clamp-2">
                    {file.description}
                  </p>
                </button>
              );
            })}
          </div>

          {/* AST Symbol & Inspection Panel */}
          <div className="lg:col-span-2 bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-border/60 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-bold text-foreground">
                    {selectedFile.path}
                  </span>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase ${
                    selectedFile.type === "test"
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      : "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                  }`}>
                    {selectedFile.type}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {selectedFile.description}
                </p>
              </div>
            </div>

            {/* Extracted AST Classes */}
            {selectedFile.classes.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5 uppercase tracking-wider">
                  <Cpu className="h-3.5 w-3.5 text-indigo-400" />
                  AST Extracted Classes
                </span>
                <div className="flex flex-wrap gap-2">
                  {selectedFile.classes.map((cls, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-mono text-xs"
                    >
                      class {cls}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted AST Functions */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5 uppercase tracking-wider">
                <Code2 className="h-3.5 w-3.5 text-cyan-400" />
                AST Extracted Functions / Methods
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {selectedFile.functions.map((fn, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-secondary/30 border border-border/70 font-mono text-xs flex items-center justify-between text-zinc-200"
                  >
                    <span>def {fn}()</span>
                    <span className="text-[10px] text-muted-foreground">Indexed in Qdrant</span>
                  </div>
                ))}
              </div>
            </div>

            {/* RAG Knowledge Base Integration Status */}
            <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-xs space-y-1">
              <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Qdrant Hybrid Retrieval Ready
              </div>
              <p className="text-muted-foreground text-[11px]">
                This file&apos;s AST nodes have been segmented into semantic chunk vectors (1536 dimensions) and lexical inverted indices for automated multi-agent incident diagnosis.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
