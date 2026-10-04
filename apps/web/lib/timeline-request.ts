// Fitting dates is browser interaction state. Only changes to the actual
// server filters should fetch another page; cursors and repeated filters stay.
export function timelineRequestKey(params: URLSearchParams, defaults?: { start: number; end: number }): string {
  const request = new URLSearchParams(params);
  request.delete("fit");
  // Leave incomplete/malformed shared ranges for the server to reject.
  if (defaults && !request.has("start") && !request.has("end")) {
    request.set("start", String(defaults.start));
    request.set("end", String(defaults.end));
  }
  request.sort();
  return request.toString();
}
