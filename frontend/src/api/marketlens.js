const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options
    });
  } catch {
    throw new Error(
      "Could not reach the MarketLens API. Confirm the backend is running."
    );
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      // The status code still provides a useful fallback error.
    }
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return response.json();
}

export function getOverview() {
  return request("/api/overview");
}

export function getCities({ limit, state } = {}) {
  const params = new URLSearchParams();
  if (limit) params.set("limit", limit);
  if (state) params.set("state", state);
  const query = params.toString();
  return request(`/api/cities${query ? `?${query}` : ""}`);
}

export function getCity(city) {
  return request(`/api/cities/${encodeURIComponent(city)}`);
}

export function getStates() {
  return request("/api/states");
}

export function recalculateScores(weights) {
  return request("/api/score", {
    method: "POST",
    body: JSON.stringify(weights)
  });
}

export function generateExecutiveInsights() {
  return request("/api/ai/insights", { method: "POST" });
}

export function compareCities(cityA, cityB) {
  return request("/api/ai/compare", {
    method: "POST",
    body: JSON.stringify({ city_a: cityA, city_b: cityB })
  });
}

export function askMarketLens(question) {
  return request("/api/ai/ask", {
    method: "POST",
    body: JSON.stringify({ question })
  });
}
