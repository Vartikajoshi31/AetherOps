"use client";

import { useState, useEffect } from "react";
import {
  Database,
  Search,
  Cpu,
  Layers,
  CheckCircle2,
  AlertCircle,
  FileCode2,
  Sparkles,
  RefreshCw,
  ExternalLink,
  SlidersHorizontal,
  Activity,
  Copy,
  Check
} from "lucide-react";
import { api } from "@/lib/api";

interface RAGStats {
  collection_name: string;
  vector_dimension: number;
  total_points_indexed: number;
  status: string;
}

interface SearchResult {
  id: string;
  content: string;
  file_path: string;
  doc_type: string;
  function_name?: string | null;
  class_name?: string | null;
  line_start: number;
  line_end: number;
  combined_score: number;
  vector_score: number;
  keyword_match_score: number;
  source_attribution: {
    repository: string;
    file_path: string;
    lines: string;
    function: string;
    commit: string;
  };
}

interface EvaluationDetail {
  query: string;
  top_k: number;
  retrieved_count: number;
  expected_culprit_files: string[];
  retrieved_files: string[];
  precision_at_k: number;
  recall_at_k: number;
  mrr: number;
  passed_threshold: boolean;
}

interface EvaluationReport {
  total_queries_evaluated: number;
  mean_precision: number;
  mean_recall: number;
  mean_reciprocal_rank: number;
  eval_details: EvaluationDetail[];
}

export default function RAGPage() {
  const [stats, setStats] = useState<RAGStats | null>(null);
  const [query, setQuery] = useState("QueuePool limit of size 10 overflow reached database connection leak");
  const [limit, setLimit] = useState(5);
  const [fileHint, setFileHint] = useState("");
  const [funcHint, setFuncHint] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Evaluation Suite State
  const [evalReport, setEvalReport] = useState<EvaluationReport | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await api.getRAGStats();
      setStats(data);
    } catch (e: any) {
      console.error("Failed to load RAG stats", e);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setSearchError(null);
    try {
      const res = await api.searchRAG(query, limit, fileHint.trim() || undefined, funcHint.trim() || undefined);
      setResults(res);
    } catch (e: any) {
      setSearchError(e.message || "Failed to search knowledge base");
    } finally {
      setIsSearching(false);
    }
  };

  const handleRunEvaluation = async () => {
    setIsEvaluating(true);
    try {
      const report = await api.evaluateRAG();
      setEvalReport(report);
    } catch (e: any) {
      console.error("Evaluation failed", e);
    } finally {
      setIsEvaluating(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/60 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              RAG & Hybrid Telemetry Engine
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-medium">
              Qdrant Dense + BM25 Lexical
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            AST-aware code chunking, Reciprocal Rank Fusion (RRF), and real-time incident knowledge retrieval.
          </p>
        </div>

        {/* Index Stats Pill */}
        <div className="flex items-center gap-3">
          <button
            onClick={loadStats}
            className="p-2 text-muted-foreground hover:text-foreground rounded-lg border border-border bg-card/50 transition-colors"
            title="Refresh Stats"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <div className="bg-card border border-border rounded-lg px-4 py-2 flex items-center gap-4 text-xs font-mono">
            <div>
              <span className="text-muted-foreground">Collection: </span>
              <span className="text-foreground font-semibold">{stats?.collection_name || "agentops_kb"}</span>
            </div>
            <div className="h-4 w-px bg-border" />
            <div>
              <span className="text-muted-foreground">Vector Dims: </span>
              <span className="text-cyan-400 font-semibold">{stats?.vector_dimension || 1536}</span>
            </div>
            <div className="h-4 w-px bg-border" />
            <div>
              <span className="text-muted-foreground">Indexed Chunks: </span>
              <span className="text-emerald-400 font-semibold">{stats?.total_points_indexed ?? 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Search & Results */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Search Query & Parameters */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Search className="h-4 w-4 text-primary" />
                Hybrid Code Search
              </h2>
              <span className="text-[11px] text-muted-foreground font-mono">RRF k=60</span>
            </div>

            <form onSubmit={handleSearch} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1.5">
                  Natural Language or Stack Trace Query
                </label>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  rows={4}
                  placeholder="Paste error logs, function names, or symptoms..."
                  className="w-full bg-background border border-input rounded-lg px-3 py-2 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span>Candidate Limit (Top K)</span>
                  <span className="font-mono text-foreground">{limit}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="15"
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  className="w-full accent-primary"
                />
              </div>

              <div className="pt-2 border-t border-border/60">
                <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <SlidersHorizontal className="h-3 w-3" />
                  Reranking Hints (Optional)
                </p>
                <div className="space-y-2">
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Target File Hint</label>
                    <input
                      type="text"
                      value={fileHint}
                      onChange={(e) => setFileHint(e.target.value)}
                      placeholder="e.g. checkout-service/db.py"
                      className="w-full bg-background border border-input rounded-md px-2.5 py-1.5 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Target Function Hint</label>
                    <input
                      type="text"
                      value={funcHint}
                      onChange={(e) => setFuncHint(e.target.value)}
                      placeholder="e.g. acquire"
                      className="w-full bg-background border border-input rounded-md px-2.5 py-1.5 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={isSearching || !query.trim()}
                className="w-full py-2.5 px-4 rounded-lg bg-primary text-primary-foreground font-medium text-xs flex items-center justify-center gap-2 hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {isSearching ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    Querying Qdrant & BM25...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-3.5 w-3.5" />
                    Execute Hybrid Retrieval
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Quick Benchmark Queries */}
          <div className="bg-card border border-border rounded-xl p-4 shadow-sm space-y-3">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Quick Test Queries
            </h3>
            <div className="space-y-1.5">
              {[
                { label: "Connection Pool Exhaustion", q: "QueuePool limit of size 10 overflow reached database connection leak" },
                { label: "Payment Thundering Herd", q: "deterministic exponential backoff thundering herd retry without jitter" },
                { label: "Order Null Pointer Dereference", q: "AttributeError NoneType object has no attribute country_code shipping" },
                { label: "Inventory Unbounded Cache Leak", q: "unbounded cache memory leak SKU invalidation TTL eviction" }
              ].map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setQuery(item.q);
                    setTimeout(() => handleSearch(), 50);
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg bg-secondary/40 hover:bg-secondary/70 border border-border/50 text-xs text-foreground/90 transition-colors flex items-center justify-between group"
                >
                  <span className="truncate">{item.label}</span>
                  <Search className="h-3 w-3 text-muted-foreground group-hover:text-primary shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Columns: Retrieved Results */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <FileCode2 className="h-4 w-4 text-cyan-400" />
              Retrieved Technical Evidence ({results.length})
            </h2>
            {results.length > 0 && (
              <span className="text-xs text-muted-foreground">
                Grounded source snippets with line attribution
              </span>
            )}
          </div>

          {searchError && (
            <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{searchError}</span>
            </div>
          )}

          {results.length === 0 && !isSearching && (
            <div className="p-12 text-center border border-dashed border-border rounded-xl bg-card/30">
              <Database className="h-8 w-8 text-muted-foreground/50 mx-auto mb-3" />
              <p className="text-sm font-medium text-foreground">No evidence retrieved yet</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                Execute a query or click a quick scenario to inspect semantic chunk retrieval and source attribution.
              </p>
            </div>
          )}

          <div className="space-y-4">
            {results.map((item, idx) => {
              const isCopied = copiedId === item.id;
              return (
                <div
                  key={item.id || idx}
                  className="bg-card border border-border rounded-xl overflow-hidden shadow-sm hover:border-border/80 transition-all"
                >
                  {/* Result Header Bar */}
                  <div className="px-4 py-2.5 bg-secondary/30 border-b border-border/60 flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="px-2 py-0.5 rounded bg-primary/20 text-primary font-mono text-[11px] font-semibold">
                        #{idx + 1}
                      </span>
                      <span className="font-mono text-foreground font-medium">
                        {item.file_path}
                      </span>
                      <span className="text-muted-foreground font-mono text-[11px]">
                        :{item.line_start}-{item.line_end}
                      </span>
                      {item.function_name && (
                        <span className="px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-mono text-[10px]">
                          fn: {item.function_name}
                        </span>
                      )}
                      <span className="px-1.5 py-0.5 rounded bg-muted text-muted-foreground text-[10px] uppercase font-mono">
                        {item.doc_type}
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2 text-[11px] font-mono">
                        <span className="text-muted-foreground">Score:</span>
                        <span className="text-emerald-400 font-bold">
                          {(item.combined_score * 100).toFixed(1)}
                        </span>
                        <span className="text-muted-foreground/60 text-[10px]">
                          (vec: {(item.vector_score * 100).toFixed(0)}% / key: {(item.keyword_match_score * 100).toFixed(0)}%)
                        </span>
                      </div>
                      <button
                        onClick={() => copyToClipboard(item.content, item.id)}
                        className="p-1 text-muted-foreground hover:text-foreground rounded transition-colors"
                        title="Copy chunk"
                      >
                        {isCopied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </div>

                  {/* Code Snippet Box */}
                  <div className="p-4 bg-black/40 overflow-x-auto">
                    <pre className="text-xs font-mono text-zinc-300 leading-relaxed whitespace-pre">
                      <code>{item.content}</code>
                    </pre>
                  </div>

                  {/* Footer Attribution */}
                  <div className="px-4 py-2 bg-secondary/10 border-t border-border/40 text-[11px] text-muted-foreground font-mono flex items-center justify-between">
                    <span>Repo: {item.source_attribution?.repository || "acme/ecommerce-platform"}</span>
                    <span>Commit: {item.source_attribution?.commit?.substring(0, 7) || "main"}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* RAG Evaluation Benchmark Suite Section */}
      <div className="border border-border rounded-xl bg-card p-6 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/60 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-indigo-400" />
              <h2 className="text-base font-semibold text-foreground">
                Automated RAG Retrieval Evaluation Suite
              </h2>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Measures Precision@K, Recall@K, and Mean Reciprocal Rank (MRR) across all benchmark failure scenarios.
            </p>
          </div>

          <button
            onClick={handleRunEvaluation}
            disabled={isEvaluating}
            className="py-2 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            {isEvaluating ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                Evaluating Benchmark Suite...
              </>
            ) : (
              <>
                <Sparkles className="h-3.5 w-3.5" />
                Run RAG Benchmark Evaluation
              </>
            )}
          </button>
        </div>

        {evalReport ? (
          <div className="space-y-6">
            {/* Metric KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-secondary/30 border border-border">
                <span className="text-xs text-muted-foreground block">Mean Precision@5</span>
                <span className="text-2xl font-bold font-mono text-cyan-400 mt-1 block">
                  {(evalReport.mean_precision * 100).toFixed(1)}%
                </span>
                <span className="text-[11px] text-muted-foreground">Relevant chunks in top 5</span>
              </div>
              <div className="p-4 rounded-lg bg-secondary/30 border border-border">
                <span className="text-xs text-muted-foreground block">Mean Recall@5</span>
                <span className="text-2xl font-bold font-mono text-emerald-400 mt-1 block">
                  {(evalReport.mean_recall * 100).toFixed(1)}%
                </span>
                <span className="text-[11px] text-muted-foreground">Culprit files retrieved</span>
              </div>
              <div className="p-4 rounded-lg bg-secondary/30 border border-border">
                <span className="text-xs text-muted-foreground block">Mean Reciprocal Rank (MRR)</span>
                <span className="text-2xl font-bold font-mono text-purple-400 mt-1 block">
                  {evalReport.mean_reciprocal_rank.toFixed(3)}
                </span>
                <span className="text-[11px] text-muted-foreground">Rank of first valid hit</span>
              </div>
            </div>

            {/* Evaluation Query Details Table */}
            <div
              tabIndex={0}
              role="region"
              aria-labelledby="eval-table-heading"
              className="overflow-x-auto rounded-lg border border-border bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <table className="w-full text-xs text-left">
                <thead className="bg-secondary/40 text-muted-foreground uppercase text-[10px] font-mono tracking-wider border-b border-border">
                  <tr>
                    <th scope="col" className="p-3">Scenario / Query</th>
                    <th scope="col" className="p-3">Expected Culprit Files</th>
                    <th scope="col" className="p-3">Retrieved Files</th>
                    <th scope="col" className="p-3 text-right">Precision@K</th>
                    <th scope="col" className="p-3 text-right">Recall@K</th>
                    <th scope="col" className="p-3 text-right">MRR</th>
                    <th scope="col" className="p-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60 font-mono">
                  {evalReport.eval_details.map((detail, idx) => (
                    <tr key={idx} className="hover:bg-muted/30">
                      <td className="p-3 max-w-xs font-sans text-foreground">
                        <p className="truncate font-medium">{detail.query}</p>
                      </td>
                      <td className="p-3 text-muted-foreground">
                        {detail.expected_culprit_files.map((f, i) => (
                          <span key={i} className="block text-[11px]">{f}</span>
                        ))}
                      </td>
                      <td className="p-3 text-muted-foreground">
                        {detail.retrieved_files.slice(0, 2).map((f, i) => (
                          <span key={i} className="block text-[11px] text-zinc-300">{f}</span>
                        ))}
                        {detail.retrieved_files.length > 2 && (
                          <span className="text-[10px] text-muted-foreground">
                            +{detail.retrieved_files.length - 2} more
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-right text-cyan-400 font-semibold">
                        {(detail.precision_at_k * 100).toFixed(0)}%
                      </td>
                      <td className="p-3 text-right text-emerald-400 font-semibold">
                        {(detail.recall_at_k * 100).toFixed(0)}%
                      </td>
                      <td className="p-3 text-right text-purple-400 font-semibold">
                        {detail.mrr.toFixed(2)}
                      </td>
                      <td className="p-3 text-center">
                        {detail.passed_threshold ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                            <CheckCircle2 className="h-3 w-3" /> PASS
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                            <AlertCircle className="h-3 w-3" /> RETRY
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center border border-dashed border-border rounded-lg bg-card/20">
            <p className="text-xs text-muted-foreground">
              Click &quot;Run RAG Benchmark Evaluation&quot; to execute automated accuracy metrics across all production incident scenarios.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
