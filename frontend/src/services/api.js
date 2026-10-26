/**
 * JobShield AI Backend API Service
 * Handles communication with the FastAPI service endpoints.
 * Automatically discovers active backend port (configured for port 8008).
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8008/api';

const CANDIDATE_BASE_URLS = [
  API_BASE_URL,
  'http://127.0.0.1:8008/api',
].filter(Boolean);

let activeBaseUrl = CANDIDATE_BASE_URLS[0];

/**
 * Fetch service health status from FastAPI backend
 * @returns {Promise<{ ok: boolean, data?: any, error?: string, url?: string }>}
 */
export async function checkBackendHealth() {
  const urlsToTry = Array.from(new Set([activeBaseUrl, ...CANDIDATE_BASE_URLS]));

  for (const baseUrl of urlsToTry) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);

      const response = await fetch(`${baseUrl}/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        activeBaseUrl = baseUrl;
        return { ok: true, data, url: baseUrl };
      }
    } catch {
      // Continue to next candidate URL
    }
  }

  return {
    ok: false,
    error: 'Backend offline or unreachable. Start the FastAPI server on port 8008.',
  };
}

/**
 * Submit job posting for live ML fraud analysis
 * @param {Object} jobData
 * @returns {Promise<{ ok: boolean, data?: any, error?: string }>}
 */
export async function analyzeJob(jobData) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    const response = await fetch(`${activeBaseUrl}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(jobData),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      return { ok: true, data };
    }

    const errData = await response.json().catch(() => ({}));
    return {
      ok: false,
      error: errData.detail || `Analysis request failed with status ${response.status}`,
    };
  } catch (err) {
    return {
      ok: false,
      error: err.name === 'AbortError' ? 'Analysis timed out.' : (err.message || 'Network error connecting to backend.'),
    };
  }
}

/**
 * Fetch candidate model comparison and benchmark evaluation metrics
 * @returns {Promise<{ ok: boolean, data?: any, error?: string }>}
 */
export async function fetchModelMetrics() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${activeBaseUrl}/metrics`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      return { ok: true, data };
    }

    const errData = await response.json().catch(() => ({}));
    return {
      ok: false,
      error: errData.detail || `Failed to fetch metrics: ${response.status}`,
    };
  } catch (err) {
    return {
      ok: false,
      error: err.message || 'Network error fetching model metrics.',
    };
  }
}

export function getActiveApiUrl() {
  return activeBaseUrl;
}
