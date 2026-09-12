export function e2eEditorToken(): string {
  const token = process.env.ARTLINE_E2E_EDITOR_TOKEN;
  if (!token) {
    throw new Error("Set ARTLINE_E2E_EDITOR_TOKEN for editor browser tests against a disposable test environment.");
  }
  return token;
}
