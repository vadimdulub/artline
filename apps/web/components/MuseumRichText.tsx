"use client";
import { useId, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import styles from "./MuseumStudio.module.css";
export function MuseumRichText({ label, value, onChange, disabled = false }: { label: string; value: string; onChange: (value: string) => void; disabled?: boolean }) {
  const [preview, setPreview] = useState(false);
  const input = useRef<HTMLTextAreaElement>(null), id = useId();
  function format(before: string, after = "", placeholder = "Text") {
    const element = input.current; if (!element) return;
    const start = element.selectionStart, end = element.selectionEnd, selected = value.slice(start, end) || placeholder;
    const next = value.slice(0, start) + before + selected + after + value.slice(end);
    if (next.length > 20000) return;
    onChange(next); requestAnimationFrame(() => { element.focus(); element.setSelectionRange(start + before.length, start + before.length + selected.length); });
  }
  return <div className={styles.richText}><label htmlFor={id}>{label} <span className={styles.requirement}>Optional</span></label><div className={styles.formatBar} role="group" aria-label={`${label} formatting`}>
    <button type="button" disabled={preview || disabled} onClick={() => format("**", "**")}><strong>Bold</strong></button><button type="button" disabled={preview || disabled} onClick={() => format("*", "*")}><em>Italic</em></button><button type="button" disabled={preview || disabled} onClick={() => format("\n\n## ", "\n\n", "Heading")}>Heading</button><button type="button" disabled={preview || disabled} onClick={() => format("\n- ", "\n", "List item")}>List</button><button type="button" disabled={preview || disabled} onClick={() => format("[", "](https://)", "Link text")}>Link</button><button type="button" disabled={disabled} aria-pressed={preview} onClick={() => setPreview(v => !v)}>{preview ? "Write" : "Preview"}</button>
  </div>{preview ? <div className={styles.textPreview} role="region" aria-label={`${label} preview`}>{value ? <ReactMarkdown skipHtml disallowedElements={["img"]} components={{ h1: ({ children }) => <h2>{children}</h2> }}>{value}</ReactMarkdown> : <p>Add some text to preview it here.</p>}</div> : <textarea id={id} ref={input} rows={7} maxLength={20000} value={value} disabled={disabled} onChange={e => onChange(e.target.value)} />}</div>;
}
