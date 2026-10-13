import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import AnalyzePage from './pages/AnalyzePage';
import ResultsPage from './pages/ResultsPage';
import PerformancePage from './pages/PerformancePage';
import { checkBackendHealth } from './services/api';

function AppLayout() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [backendHealth, setBackendHealth] = useState(null);
  const [backendLoading, setBackendLoading] = useState(true);
  const [backendError, setBackendError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  const fetchHealth = useCallback(async () => {
    setBackendLoading(true);
    setBackendError(null);
    const res = await checkBackendHealth();
    if (res.ok) {
      setBackendHealth(res.data);
      setBackendError(null);
    } else {
      setBackendError(res.error || 'Failed to connect');
    }
    setBackendLoading(false);
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  // Determine current page title
  const getPageInfo = () => {
    switch (location.pathname) {
      case '/analyze':
        return { title: 'Analyze Job Opportunity', category: 'Inference Engine' };
      case '/results':
        return { title: 'Analysis Results & Evidence', category: 'Intelligence' };
      case '/performance':
        return { title: 'Model Performance & Benchmarks', category: 'ML Evaluation' };
      case '/':
      default:
        return { title: 'Security Dashboard', category: 'Overview' };
    }
  };

  const pageInfo = getPageInfo();

  return (
    <div className="min-h-screen bg-shield-bg text-shield-text flex">
      {/* Permanent / Responsive Sidebar */}
      <Sidebar
        backendHealth={backendHealth}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0 min-h-screen">
        <Navbar
          pageTitle={pageInfo.title}
          pageCategory={pageInfo.category}
          backendHealth={backendHealth}
          backendLoading={backendLoading}
          backendError={backendError}
          onRefreshHealth={fetchHealth}
          setMobileOpen={setMobileOpen}
        />

        <main className="flex-1 p-4 md:p-6 lg:p-8">
          <Routes>
            <Route
              path="/"
              element={
                <DashboardPage
                  backendHealth={backendHealth}
                  backendError={backendError}
                />
              }
            />
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
            <Route
              path="/results"
              element={<ResultsPage analysisResult={analysisResult} />}
            />
            <Route
              path="/performance"
              element={<PerformancePage backendHealth={backendHealth} />}
            />
            <Route
              path="*"
              element={
                <DashboardPage
                  backendHealth={backendHealth}
                  backendError={backendError}
                />
              }
            />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
