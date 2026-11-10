/**
 * JobShield AI Backend API Service
 * Handles communication with the FastAPI service endpoints.
 * Automatically discovers active backend port (supports port 8001 and port 8008).
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api';

const CANDIDATE_BASE_URLS = [
  API_BASE_URL,
  'http://127.0.0.1:8001/api',
  'http://localhost:8001/api',
  'http://127.0.0.1:8008/api',
  'http://localhost:8008/api',
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
    error: 'Backend offline or unreachable. Start the FastAPI server on port 8001 or 8008.',
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
 * Extract structured 20-field job posting data from a URL with SSRF protection
 * @param {string} url
 * @returns {Promise<{ ok: boolean, data?: any, error?: string }>}
 */
export async function extractFromUrl(url) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);

    const response = await fetch(`${activeBaseUrl}/extract/url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ url }),
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
      error: errData.detail || `Extraction failed with status ${response.status}`,
    };
  } catch (err) {
    return {
      ok: false,
      error: err.name === 'AbortError' ? 'Extraction timed out.' : (err.message || 'Network error during URL extraction.'),
    };
  }
}

/**
 * Extract structured job posting data from raw pasted text
 * @param {string} text
 * @returns {Promise<{ ok: boolean, data?: any, error?: string }>}
 */
export async function extractFromText(text) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    const response = await fetch(`${activeBaseUrl}/extract/text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ text }),
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
      error: errData.detail || `Text extraction failed with status ${response.status}`,
    };
  } catch (err) {
    return {
      ok: false,
      error: err.name === 'AbortError' ? 'Extraction timed out.' : (err.message || 'Network error during text extraction.'),
    };
  }
}

/**
 * Request detailed grounded AI explanation for a job posting
 * @param {Object} jobData
 * @returns {Promise<{ ok: boolean, data?: any, error?: string }>}
 */
export async function requestExplanation(jobData) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    const response = await fetch(`${activeBaseUrl}/explain`, {
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
      error: errData.detail || `Explanation request failed with status ${response.status}`,
    };
  } catch (err) {
    return {
      ok: false,
      error: err.name === 'AbortError' ? 'Explanation request timed out.' : (err.message || 'Network error requesting explanation.'),
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

/**
 * Fetch external dataset validation benchmark comparison
 * @returns {Promise<{ ok: boolean, data?: any, error?: string }>}
 */
export async function fetchExternalValidation() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(`${activeBaseUrl}/validation/external`, {
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
      error: errData.detail || `Failed to fetch external validation: ${response.status}`,
    };
  } catch (err) {
    return {
      ok: false,
      error: err.message || 'Network error fetching external validation.',
    };
  }
}

export function getActiveApiUrl() {
  return activeBaseUrl;
}

export function getDocsUrl() {
  return activeBaseUrl ? activeBaseUrl.replace(/\/api$/, '/docs') : 'http://127.0.0.1:8001/docs';
}

/**
 * Fetch paginated list of saved analyses with optional filters
 * @param {Object} params - page, page_size, search_title, search_company, classification, risk_level
 * @returns {Promise<{ ok: boolean, data?: any, error?: string }>}
 */
export async function fetchAnalyses(params = {}) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.set(k, v);
    });

    const response = await fetch(`${activeBaseUrl}/analyses?${query.toString()}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
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
      error: errData.detail || `Failed to fetch analyses: ${response.status}`,
    };
  } catch (err) {
    return {
      ok: false,
      error: err.name === 'AbortError' ? 'Request timed out.' : (err.message || 'Network error fetching analyses.'),
    };
  }
}

/**
 * Fetch aggregate stats for saved analyses (total, fraudulent, legitimate, today)
 * @returns {Promise<{ ok: boolean, data?: any, error?: string }>}
 */
export async function fetchAnalysisStats() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(`${activeBaseUrl}/analyses/stats`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
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
      error: errData.detail || `Failed to fetch analysis stats: ${response.status}`,
    };
  } catch (err) {
    return {
      ok: false,
      error: err.name === 'AbortError' ? 'Request timed out.' : (err.message || 'Network error fetching stats.'),
    };
  }
}

/**
 * Fetch full detail record for a single saved analysis
 * @param {string|number} id
 * @returns {Promise<{ ok: boolean, data?: any, error?: string }>}
 */
export async function fetchAnalysisDetail(id) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(`${activeBaseUrl}/analyses/${id}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      return { ok: true, data };
    }

    if (response.status === 404) {
      return { ok: false, error: 'Analysis not found.', status: 404 };
    }

    const errData = await response.json().catch(() => ({}));
    return {
      ok: false,
      error: errData.detail || `Failed to fetch analysis detail: ${response.status}`,
    };
  } catch (err) {
    return {
      ok: false,
      error: err.name === 'AbortError' ? 'Request timed out.' : (err.message || 'Network error fetching analysis detail.'),
    };
  }
}

/**
 * Delete a saved analysis record by ID
 * @param {string|number} id
 * @returns {Promise<{ ok: boolean, error?: string }>}
 */
export async function deleteAnalysis(id) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(`${activeBaseUrl}/analyses/${id}`, {
      method: 'DELETE',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      return { ok: true };
    }

    const errData = await response.json().catch(() => ({}));
    return {
      ok: false,
      error: errData.detail || `Failed to delete analysis: ${response.status}`,
    };
  } catch (err) {
    return {
      ok: false,
      error: err.name === 'AbortError' ? 'Request timed out.' : (err.message || 'Network error deleting analysis.'),
    };
  }
}
