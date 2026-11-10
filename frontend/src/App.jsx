import React, { useState, useEffect, useCallback } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingNavbar from "./components/LandingNavbar";
import ErrorBoundary from "./components/ErrorBoundary";
import LandingPage from "./pages/LandingPage";
import AnalyzePage from "./pages/AnalyzePage";
import ResultsPage from "./pages/ResultsPage";
import PerformancePage from "./pages/PerformancePage";
import HistoryPage from "./pages/HistoryPage";
import AnalysisDetailPage from "./pages/AnalysisDetailPage";
import NotFoundPage from "./pages/NotFoundPage";
import { checkBackendHealth } from "./services/api";

function AppShell() {
  const [backendHealth, setBackendHealth] = useState(null);
  const [backendLoading, setBackendLoading] = useState(true);
  const [backendError, setBackendError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  const fetchHealth = useCallback(async () => {
    setBackendLoading(true);
    setBackendError(null);
    try {
      const res = await checkBackendHealth();
      if (res.ok) {
        setBackendHealth(res.data);
      } else {
        setBackendError(res.error || "Failed to connect to backend service.");
      }
    } catch (err) {
      setBackendError(err.message || "Network error connecting to backend.");
    } finally {
      setBackendLoading(false);
    }
  }, []);

  useEffect(() => { fetchHealth(); }, [fetchHealth]);

  return (
    <div className="min-h-screen bg-[#101114] text-[#F2F4F6] flex flex-col">
      <LandingNavbar backendHealth={backendHealth} backendLoading={backendLoading} backendError={backendError} />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/analyze"
            element={
              <AnalyzePage
                backendHealth={backendHealth}
                backendError={backendError}
                onNavigateToResults={(result) => setAnalysisResult(result)}
              />
            }
          />
          <Route path="/results" element={<ResultsPage analysisResult={analysisResult} />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/history/:id" element={<AnalysisDetailPage />} />
          <Route path="/performance" element={<PerformancePage backendHealth={backendHealth} />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <AppShell />
      </ErrorBoundary>
    </BrowserRouter>
  );
}
