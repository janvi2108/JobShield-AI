/**
 * JobShield AI Backend API Service
 * Handles communication with the FastAPI service endpoints.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

/**
 * Fetch service health status from FastAPI backend
 * @returns {Promise<{ ok: boolean, data?: any, error?: string }>}
 */
export async function checkBackendHealth() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        ok: false,
        error: `HTTP Error ${response.status}: ${response.statusText}`,
      };
    }

    const data = await response.json();
    return { ok: true, data };
  } catch (err) {
    if (err.name === 'AbortError') {
      return { ok: false, error: 'Connection timed out (backend unreachable at ' + API_BASE_URL + ')' };
    }
    return {
      ok: false,
      error: 'Backend offline or unreachable. Start the FastAPI server on port 8000.',
    };
  }
}

export { API_BASE_URL };
