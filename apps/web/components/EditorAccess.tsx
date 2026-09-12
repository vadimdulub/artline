"use client";
import { useSyncExternalStore } from "react";
const key = "artline-editor-token";
function subscribe(callback: () => void) { window.addEventListener("artline:editor", callback); return () => window.removeEventListener("artline:editor", callback); }
function read() { try { return sessionStorage.getItem(key) ?? ""; } catch { return ""; } }
export function useEditorToken(): [string, (value: string) => void] {
  const token = useSyncExternalStore(subscribe, read, () => "");
  return [token, value => { try { if (value) sessionStorage.setItem(key, value); else sessionStorage.removeItem(key); } catch {} window.dispatchEvent(new Event("artline:editor")); }];
}
export function EditorAccess({ token, onChange }: { token: string; onChange: (value: string) => void }) {
  return <section className="editor-access"><div><h2>{token ? "Editor access" : "Read-only preview"}</h2><p>{token ? "Your token is kept only for this browser session. Every change is checked by the server." : "Browse the catalogue here. Enter your editor token to enable saving, checking, and archiving records."}</p>{token && <button type="button" className="text-button" onClick={() => onChange("")}>Clear editor token</button>}</div><label><span>Editor token</span><input type="password" autoComplete="off" value={token} onChange={event => onChange(event.target.value)} placeholder="Your editor token" /></label></section>;
}
