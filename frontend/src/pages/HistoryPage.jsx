import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  FileText,
  Search,
  Filter,
  Trash2,
  Eye,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldAlert,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import EmptyState from "../components/EmptyState";
import { fetchAnalyses, fetchAnalysisStats, deleteAnalysis } from "../services/api";

export default function HistoryPage() {
  const navigate = useNavigate();

  // State
  const [analyses, setAnalyses] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const [searchTitle, setSearchTitle] = useState("");
  const [searchCompany, setSearchCompany] = useState("");
  const [classification, setClassification] = useState("");
  const [riskLevel, setRiskLevel] = useState("");

  // Delete modal state
  const [deleteTargetId, setDeleteTargetId] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Load live statistics
  const loadStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const res = await fetchAnalysisStats();
      if (res.ok) {
        setStats(res.data);
      }
    } catch {
      // Non-blocking stats fetch
    } finally {
      setStatsLoading(false);
    }
  }, []);

  // Load paginated analyses
  const loadAnalyses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (searchTitle.trim()) params.search_title = searchTitle.trim();
      if (searchCompany.trim()) params.search_company = searchCompany.trim();
      if (classification) params.classification = classification;
      if (riskLevel) params.risk_level = riskLevel;

      const res = await fetchAnalyses(params);
      if (res.ok && res.data) {
        setAnalyses(res.data.analyses || res.data.data || []);
        if (res.data.pagination) {
          setTotalPages(res.data.pagination.total_pages || 1);
          setTotalCount(res.data.pagination.total_count || 0);
        } else {
          setTotalCount(res.data.total_count || 0);
          setTotalPages(res.data.total_pages || 1);
        }
      } else {
        setError(res.error || "Failed to retrieve analysis history from local database.");
      }
    } catch (err) {
      setError(err.message || "Network error loading analysis history.");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchTitle, searchCompany, classification, riskLevel]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  useEffect(() => {
    loadAnalyses();
  }, [loadAnalyses]);

  const handleClearFilters = () => {
    setSearchTitle("");
    setSearchCompany("");
    setClassification("");
    setRiskLevel("");
    setPage(1);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadAnalyses();
  };

  const confirmDelete = async () => {
    if (!deleteTargetId) return;
    setDeleting(true);
    try {
      const res = await deleteAnalysis(deleteTargetId);
      if (res.ok) {
        setDeleteTargetId(null);
        await Promise.all([loadAnalyses(), loadStats()]);
      } else {
        alert(res.error || "Could not delete analysis.");
      }
    } catch (err) {
      alert("Error deleting analysis: " + err.message);
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (isoStr) => {
    if (!isoStr) return "Unknown";
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-shield-border pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#D9B100] font-semibold bg-[#D9B100]/10 px-2.5 py-0.5 rounded border border-[#D9B100]/30">
              Audit Telemetry & Audit Logs
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-shield-text">
            Analysis History
          </h1>
          <p className="text-sm text-shield-muted mt-1">
            Persistent local records of evaluated job postings, fraud probabilities, and explainability evidence.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => { loadAnalyses(); loadStats(); }}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-md bg-shield-card hover:bg-shield-surface border border-shield-border text-shield-text text-xs font-mono transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-[#D9B100] hover:bg-[#e5bc05] text-black font-semibold text-xs font-mono transition-colors shadow-sm"
          >
            + Analyze New Job
          </Link>
        </div>
      </div>

      {/* Aggregate Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 font-mono">
        <div className="p-4 rounded-lg bg-shield-card border border-shield-border">
          <div className="flex items-center justify-between text-xs text-shield-subtle mb-1">
            <span>Total Analyses</span>
            <FileText className="w-4 h-4 text-shield-subtle" />
          </div>
          <div className="text-2xl font-bold text-shield-text">
            {statsLoading ? "..." : (stats?.total_analyses ?? 0)}
          </div>
          <div className="text-[11px] text-shield-subtle mt-1">Stored in SQLite</div>
        </div>

        <div className="p-4 rounded-lg bg-shield-card border border-shield-border">
          <div className="flex items-center justify-between text-xs text-shield-subtle mb-1">
            <span>Legitimate</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            {statsLoading ? "..." : (stats?.legitimate_count ?? 0)}
          </div>
          <div className="text-[11px] text-shield-subtle mt-1">Verified safe</div>
        </div>

        <div className="p-4 rounded-lg bg-shield-card border border-shield-border">
          <div className="flex items-center justify-between text-xs text-shield-subtle mb-1">
            <span>Fraudulent</span>
            <ShieldAlert className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-2xl font-bold text-red-400">
            {statsLoading ? "..." : (stats?.fraudulent_count ?? 0)}
          </div>
          <div className="text-[11px] text-shield-subtle mt-1">Scams flagged</div>
        </div>

        <div className="p-4 rounded-lg bg-shield-card border border-shield-border">
          <div className="flex items-center justify-between text-xs text-shield-subtle mb-1">
            <span>High Risk</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">
            {statsLoading ? "..." : (stats?.high_risk_count ?? 0)}
          </div>
          <div className="text-[11px] text-shield-subtle mt-1">Critical/High tiers</div>
        </div>

        <div className="p-4 rounded-lg bg-shield-card border border-shield-border col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between text-xs text-shield-subtle mb-1">
            <span>Today's Runs</span>
            <Clock className="w-4 h-4 text-[#D9B100]" />
          </div>
          <div className="text-2xl font-bold text-[#D9B100]">
            {statsLoading ? "..." : (stats?.today_count ?? 0)}
          </div>
          <div className="text-[11px] text-shield-subtle mt-1">
            {stats?.fraud_percentage ? `${stats.fraud_percentage}% scam rate` : "No activity"}
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <form onSubmit={handleSearchSubmit} className="p-4 rounded-lg bg-shield-card border border-shield-border space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-shield-subtle" />
            <input
              type="text"
              placeholder="Filter by job title..."
              value={searchTitle}
              onChange={(e) => setSearchTitle(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded bg-shield-base border border-shield-border text-xs text-shield-text placeholder-shield-subtle focus:outline-none focus:border-[#D9B100]"
            />
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-shield-subtle" />
            <input
              type="text"
              placeholder="Filter by company..."
              value={searchCompany}
              onChange={(e) => setSearchCompany(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded bg-shield-base border border-shield-border text-xs text-shield-text placeholder-shield-subtle focus:outline-none focus:border-[#D9B100]"
            />
          </div>

          <div>
            <select
              value={classification}
              onChange={(e) => { setClassification(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 rounded bg-shield-base border border-shield-border text-xs text-shield-text focus:outline-none focus:border-[#D9B100]"
            >
              <option value="">All Classifications</option>
              <option value="fraudulent">Fraudulent Scams Only</option>
              <option value="legitimate">Legitimate Postings Only</option>
            </select>
          </div>

          <div>
            <select
              value={riskLevel}
              onChange={(e) => { setRiskLevel(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 rounded bg-shield-base border border-shield-border text-xs text-shield-text focus:outline-none focus:border-[#D9B100]"
            >
              <option value="">All Risk Tiers</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MODERATE">MODERATE</option>
              <option value="LOW">LOW</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="submit"
              className="flex-1 px-4 py-2 rounded bg-[#D9B100] hover:bg-[#e5bc05] text-black font-semibold text-xs font-mono transition-colors"
            >
              Filter
            </button>
            <button
              type="button"
              onClick={handleClearFilters}
              className="px-3 py-2 rounded bg-shield-surface border border-shield-border text-shield-muted hover:text-shield-text text-xs font-mono transition-colors"
            >
              Reset
            </button>
          </div>
        </div>
      </form>

      {/* Main Table / State Render */}
      <div className="rounded-lg bg-shield-card border border-shield-border overflow-hidden">
        {loading ? (
          <div className="p-12 text-center space-y-3 font-mono text-sm text-shield-muted">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-[#D9B100]" />
            <p>Loading analysis history from database...</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center space-y-3 font-mono text-sm">
            <AlertTriangle className="w-8 h-8 mx-auto text-red-400" />
            <p className="text-red-400 font-semibold">{error}</p>
            <button
              onClick={loadAnalyses}
              className="px-3 py-1.5 rounded bg-shield-base border border-shield-border text-xs text-shield-text hover:bg-shield-surface"
            >
              Try Again
            </button>
          </div>
        ) : analyses.length === 0 ? (
          <div className="p-10">
            <EmptyState
              icon={FileText}
              title="No Analyses Found"
              description={
                searchTitle || searchCompany || classification || riskLevel
                  ? "No saved job evaluations match your filter criteria."
                  : "No job postings have been analyzed yet. Run an analysis to store history."
              }
              actionButton={
                <Link
                  to="/analyze"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-[#D9B100] text-black text-xs font-mono font-semibold"
                >
                  Analyze a Job Opportunity
                </Link>
              }
            />
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-shield-base/80 border-b border-shield-border text-shield-subtle uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-3 px-4"># ID</th>
                    <th className="py-3 px-4">Job Title</th>
                    <th className="py-3 px-4">Company</th>
                    <th className="py-3 px-4">Classification</th>
                    <th className="py-3 px-4">Risk Probability</th>
                    <th className="py-3 px-4">Risk Tier</th>
                    <th className="py-3 px-4">Analyzed At</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-shield-border/60">
                  {analyses.map((row) => (
                    <tr key={row.id} className="hover:bg-shield-surface/30 transition-colors">
                      <td className="py-3 px-4 text-shield-subtle font-semibold">#{row.id}</td>
                      <td className="py-3 px-4 text-shield-text font-medium max-w-xs truncate">
                        <Link
                          to={`/history/${row.id}`}
                          className="hover:text-[#D9B100] hover:underline transition-colors"
                        >
                          {row.title || "Untitled Posting"}
                        </Link>
                      </td>
                      <td className="py-3 px-4 text-shield-muted max-w-[180px] truncate">
                        {row.company || "Not specified"}
                      </td>
                      <td className="py-3 px-4">
                        {row.is_fraudulent ? (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-semibold bg-red-500/10 text-red-400 border border-red-500/30">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                            Fraudulent
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                            Legitimate
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-semibold text-shield-text">
                        {(row.fraud_probability * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 px-4">
                        <StatusBadge
                          status={
                            row.risk_level === "CRITICAL"
                              ? "error"
                              : row.risk_level === "HIGH"
                              ? "warning"
                              : row.risk_level === "MODERATE"
                              ? "pending"
                              : "success"
                          }
                          label={row.risk_level}
                          size="xs"
                        />
                      </td>
                      <td className="py-3 px-4 text-shield-subtle whitespace-nowrap">
                        {formatDate(row.created_at)}
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap space-x-2">
                        <button
                          onClick={() => navigate(`/history/${row.id}`)}
                          className="p-1.5 rounded hover:bg-shield-surface text-shield-subtle hover:text-shield-text transition-colors"
                          title="View Full Analysis"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setDeleteTargetId(row.id)}
                          className="p-1.5 rounded hover:bg-red-500/10 text-shield-subtle hover:text-red-400 transition-colors"
                          title="Delete Analysis"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="p-4 border-t border-shield-border flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono text-shield-subtle">
              <div>
                Showing page <span className="text-shield-text font-bold">{page}</span> of{" "}
                <span className="text-shield-text font-bold">{totalPages}</span> ({totalCount} total analyses)
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1.5 rounded bg-shield-base border border-shield-border text-shield-text disabled:opacity-40 disabled:cursor-not-allowed hover:bg-shield-surface transition-colors flex items-center gap-1"
                >
                  <ChevronLeft className="w-3 h-3" /> Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 rounded bg-shield-base border border-shield-border text-shield-text disabled:opacity-40 disabled:cursor-not-allowed hover:bg-shield-surface transition-colors flex items-center gap-1"
                >
                  Next <ChevronRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Confirmation Modal for Deletion */}
      {deleteTargetId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="max-w-md w-full p-6 rounded-lg bg-shield-card border border-shield-border space-y-4 shadow-xl">
            <div className="flex items-center gap-3 text-red-400">
              <AlertTriangle className="w-6 h-6 flex-shrink-0" />
              <h3 className="text-base font-bold text-shield-text">Confirm Permanent Deletion</h3>
            </div>
            <p className="text-xs text-shield-muted leading-relaxed">
              Are you sure you want to delete analysis <strong className="text-shield-text font-mono">#{deleteTargetId}</strong>?
              This will permanently delete the classification, extracted fields, heuristic evidence findings, and AI explanation from the database.
            </p>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setDeleteTargetId(null)}
                disabled={deleting}
                className="px-4 py-2 rounded bg-shield-surface border border-shield-border text-xs font-mono text-shield-text hover:bg-shield-base"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDelete}
                disabled={deleting}
                className="px-4 py-2 rounded bg-red-600 hover:bg-red-700 text-white text-xs font-mono font-semibold transition-colors flex items-center gap-2"
              >
                {deleting ? "Deleting..." : "Delete Record"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

