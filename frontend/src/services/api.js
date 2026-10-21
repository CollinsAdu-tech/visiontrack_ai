/**
 * Thin wrapper around the VisionTrack AI backend. Every function either
 * resolves with the parsed JSON body or throws an Error with a
 * human-readable `.message` -- components never need to touch
 * `response.ok` or parse error bodies themselves.
 */

async function parseErrorMessage(response) {
  try {
    const body = await response.json();
    if (body && typeof body.detail === "string") return body.detail;
  } catch {
    // response wasn't JSON -- fall through to the generic message below
  }
  return `Request failed (${response.status}).`;
}

async function request(path, options) {
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new Error("Could not reach the server. Is the backend running?");
  }

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }
  return response.json();
}

export function getHealth() {
  return request("/health");
}

export function getConfig() {
  return request("/config");
}

export function detectImage(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/detect/image", { method: "POST", body: form });
}

export function trackVideo(file, { countingEnabled } = {}) {
  const form = new FormData();
  form.append("file", file);
  if (countingEnabled !== undefined) {
    form.append("counting_enabled", String(countingEnabled));
  }
  return request("/track/video", { method: "POST", body: form });
}

export function getResult(resultId) {
  return request(`/results/${resultId}`);
}
