/**
 * JobShield AI Backend API Service
 * Handles communication with the FastAPI service endpoints.
 * Automatically discovers active backend port (defaults to 8000, falls back to 8008 if 8000 is occupied).
 */

const CANDIDATE_BASE_URLS = [
  import.meta.env.VITE_API_BASE_URL,
  'http://127.0.0.1:8000/api',
  'http://127.0.0.1:8008/api',
].filter(Boolean);

let activeBaseUrl = CANDIDATE_BASE_URLS[0];

/**
 * Fetch service health status from FastAPI backend
 * @returns {Promise<{ ok: boolean, data?: any, error?: string, url?: string }>}
 */
export async function checkBackendHealth() {
  // Test active or candidate endpoints
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
    error: 'Backend offline or unreachable. Start the FastAPI server (e.g. on port 8000 or 8008).',
  };
}

export function getActiveApiUrl() {
  return activeBaseUrl;
}
