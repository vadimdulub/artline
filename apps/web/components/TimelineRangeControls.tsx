"use client";

import { useEffect, useId, useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent } from "react";
import { rangeHandlePositions } from "@/lib/range-handles";
import "./TimelineRangeControls.css";

type Drag = { kind: "start" | "end" | "window"; pointer: number; x: number; offset: number; left: number; width: number; visualStart: number; visualEnd: number; start: number; end: number; from: number; to: number };

export function TimelineRangeControls({ start, end, minimum, maximum, onChange, onPreview, endpoints, step = 1, omitYearZero = false, formatYear = String, inputPrefix = "", disabled = false, scale }: {
  start: number; end: number; minimum: number; maximum: number; onChange: (start: number, end: number) => void;
  onPreview?: (range: { start: number; end: number } | null) => void;
  endpoints: string[];
  step?: number; omitYearZero?: boolean; formatYear?: (year: number) => string; inputPrefix?: string; disabled?: boolean;
  scale?: { position: (year: number) => number; yearAt: (position: number) => number; markers?: { year: number; label: string }[] };
}) {
  const headingId = useId(), errorId = useId();
  const fromInput = useRef<HTMLInputElement>(null), toInput = useRef<HTMLInputElement>(null);
  const startHandle = useRef<HTMLInputElement>(null), endHandle = useRef<HTMLInputElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const [trackWidth, setTrackWidth] = useState(0);
  const drag = useRef<Drag | null>(null), ignoreBlur = useRef(false);
  const [preview, setPreview] = useState<{ start: number; end: number; left?: number; right?: number } | null>(null);
  const [invalid, setInvalid] = useState<{ start: number; end: number; message: string } | null>(null);
  const message = invalid?.start === start && invalid.end === end ? invalid.message : undefined;
  const shownStart = preview?.start ?? start, shownEnd = preview?.end ?? end;
  useEffect(() => { if (fromInput.current) fromInput.current.value = String(shownStart); }, [shownStart]);
  useEffect(() => { if (toInput.current) toInput.current.value = String(shownEnd); }, [shownEnd]);
  const coordinate = (value: number) => omitYearZero && value < 0 ? value + 1 : value;
  const year = (value: number) => omitYearZero && value <= 0 ? value - 1 : value;
  const a = coordinate(shownStart), b = coordinate(shownEnd), min = coordinate(minimum), max = coordinate(maximum), span = max - min;
  const position = (value: number) => scale ? scale.position(year(value)) : (value - min) / span * 100;
  const atPosition = (percent: number) => scale ? coordinate(scale.yearAt(percent)) : Math.round(min + percent / 100 * span);
  const actualLeft = position(a) / 100 * trackWidth, actualRight = position(b) / 100 * trackWidth;
  const grips = rangeHandlePositions(actualLeft, actualRight, trackWidth);
  const gripStyle = (offset: number) => ({ "--handle-offset": `${offset}px` } as CSSProperties);
  useEffect(() => {
    if (!trackRef.current) return;
    const observer = new ResizeObserver(entries => setTrackWidth(entries[0].contentRect.width));
    observer.observe(trackRef.current);
    return () => observer.disconnect();
  }, []);
  const handleValue = (value: number) => scale ? Math.round(position(value) * 1000) : value;
  const handleCoordinate = (value: string) => scale ? atPosition(Number(value) / 1000) : Number(value);
  function setCoordinates(from: number, to: number) { onChange(year(from), year(to)); }
  function pan(delta: number) {
    const width=position(b)-position(a);
    const left=Math.max(0,Math.min(100-width,position(Math.max(min,Math.min(max,a+delta)))));
    const from=atPosition(left),to=atPosition(left+width);
    setCoordinates(from,Math.max(from+1,to));
  }
  function resetFields() {
    if (fromInput.current) fromInput.current.value = String(start);
    if (toInput.current) toInput.current.value = String(end);
    setInvalid(null);
  }
  // The two fields are one draft. Tabbing between them must not clamp either
  // value against the previous range, or replace the focused DOM element.
  function commitFields(leaving = false) {
    const rawFrom = fromInput.current?.value ?? "", rawTo = toInput.current?.value ?? "";
    const from = Number(rawFrom), to = Number(rawTo);
    const error = !rawFrom || !rawTo || !Number.isInteger(from) || !Number.isInteger(to)
      ? "Enter a whole year in both fields."
      : omitYearZero && (from === 0 || to === 0) ? "There is no year zero. Use −1 for 1 BCE or 1 for the following year."
      : from < minimum || to > maximum || from > maximum || to < minimum ? `Use years from ${formatYear(minimum)} to ${formatYear(maximum)}.`
      : from >= to ? "From must be earlier than To. Edit both years, then press Enter." : null;
    if (error) {
      if (leaving) resetFields();
      setInvalid({ start, end, message: error });
    } else {
      setInvalid(null);
      if (from !== start || to !== end) onChange(from, to);
    }
  }
  function fieldKey(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") { event.preventDefault(); commitFields(); }
    if (event.key === "Escape") { event.preventDefault(); resetFields(); }
  }
  // Keyboard movement uses actual years, including the transition from 1 BCE.
  function handleKey(event: KeyboardEvent<HTMLInputElement>, from: boolean) {
    const current = from ? a : b, lower = from ? min : a + 1, upper = from ? b - 1 : max;
    const next = event.key === "Home" ? lower : event.key === "End" ? upper
      : ["ArrowLeft", "ArrowDown"].includes(event.key) ? current - 1
      : ["ArrowRight", "ArrowUp"].includes(event.key) ? current + 1
      : event.key === "PageDown" ? current - step : event.key === "PageUp" ? current + step : null;
    if (next === null) return;
    event.preventDefault();
    const bounded = Math.max(lower, Math.min(upper, next));
    setCoordinates(from ? bounded : a, from ? b : bounded);
  }
  function previewAt(x: number) {
    const d = drag.current;
    if (!d) return;
    const value = atPosition((x - d.offset - d.left) / d.width * 100);
    if (d.kind === "window") {
      const width=d.visualEnd-d.visualStart;
      const left=Math.max(0,Math.min(100-width,d.visualStart+(x-d.x)/d.width*100));
      d.from=atPosition(left);d.to=Math.max(d.from+1,atPosition(left+width));
      setPreview({start:year(d.from),end:year(d.to),left,right:left+width});
      onPreview?.({start:year(d.from),end:year(d.to)});
      return;
    } else if (d.kind === "start") d.from = Math.max(min, Math.min(d.end - 1, value));
    else d.to = Math.min(max, Math.max(d.start + 1, value));
    setPreview({ start: year(d.from), end: year(d.to) });
    onPreview?.({ start: year(d.from), end: year(d.to) });
  }
  function beginDrag(event: PointerEvent<HTMLDivElement>) {
    if (disabled || event.button !== 0 || !event.isPrimary) return;
    event.preventDefault();
    const track = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - track.left;
    const actualStart = position(a) / 100 * track.width, actualEnd = position(b) / 100 * track.width;
    const { start: left, end: right } = rangeHandlePositions(actualStart, actualEnd, track.width);
    const handle = event.target === startHandle.current || event.target === endHandle.current;
    const kind = event.target === startHandle.current ? "start" : event.target === endHandle.current ? "end"
      : x > left + 12 && x < right - 12 && b - a < span ? "window"
      : Math.abs(x - left) <= Math.abs(x - right) ? "start" : "end";
    resetFields();
    ignoreBlur.current = true;
    if (kind === "start" || kind === "end") (kind === "start" ? startHandle : endHandle).current?.focus({ preventScroll: true });
    else if (kind === "window") event.currentTarget.querySelector<HTMLButtonElement>(".range-window")?.focus({ preventScroll: true });
    ignoreBlur.current = false;
    drag.current = { kind, pointer: event.pointerId, x: event.clientX, offset: handle ? x - (kind === "start" ? actualStart : actualEnd) : 0, left: track.left, width: track.width, visualStart: position(a), visualEnd: position(b), start: a, end: b, from: a, to: b };
    event.currentTarget.setPointerCapture(event.pointerId);
    if (kind === "start" || kind === "end") previewAt(event.clientX);
  }
  function finishDrag(event: PointerEvent<HTMLDivElement>, commit: boolean) {
    const d = drag.current;
    if (!d || d.pointer !== event.pointerId) return;
    drag.current = null;
    setPreview(null);
    onPreview?.(null);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    if (commit && (d.kind === "start" || d.kind === "end")) {
      ignoreBlur.current = true;
      (d.kind === "start" ? startHandle : endHandle).current?.focus({ preventScroll: true });
      ignoreBlur.current = false;
    }
    if (commit && (d.from !== d.start || d.to !== d.end)) setCoordinates(d.from, d.to);
  }

  return <section className="timeline-focus" aria-labelledby={headingId}>
    <h2 id={headingId} className="sr-only">Timeline years</h2>
    <div ref={trackRef} className="range-track" onPointerDown={beginDrag} onPointerMove={event => { if (drag.current?.pointer === event.pointerId) previewAt(event.clientX); }} onPointerUp={event => finishDrag(event, true)} onPointerCancel={event => finishDrag(event, false)} onLostPointerCapture={event => finishDrag(event, false)}>
      <button className="range-window" type="button" disabled={disabled} aria-label="Move selected time range" style={{ left: trackWidth ? `${grips.start}px` : `${position(a)}%`, width: trackWidth ? `${grips.end - grips.start}px` : `${position(b) - position(a)}%` }}
        onKeyDown={event => { if (event.key === "ArrowLeft" || event.key === "ArrowRight") { event.preventDefault(); pan(event.key === "ArrowLeft" ? -step : step); } }}><span>Drag to move the range</span></button>
      <input ref={startHandle} className="range-handle-start" style={gripStyle(grips.start - actualLeft)} aria-label="Timeline start handle" aria-valuemin={minimum} aria-valuemax={year(b - 1)} aria-valuenow={shownStart} aria-valuetext={formatYear(shownStart)} type="range" min={scale ? 0 : min} max={scale ? 100000 : max} value={handleValue(a)} disabled={disabled} onKeyDown={event => handleKey(event, true)} onChange={event => { if (!drag.current) setCoordinates(Math.min(handleCoordinate(event.target.value), b - 1), b); }} />
      <input ref={endHandle} className="range-handle-end" style={gripStyle(grips.end - actualRight)} aria-label="Timeline end handle" aria-valuemin={year(a + 1)} aria-valuemax={maximum} aria-valuenow={shownEnd} aria-valuetext={formatYear(shownEnd)} type="range" min={scale ? 0 : min} max={scale ? 100000 : max} value={handleValue(b)} disabled={disabled} onKeyDown={event => handleKey(event, false)} onChange={event => { if (!drag.current) setCoordinates(a, Math.max(handleCoordinate(event.target.value), a + 1)); }} />
      {scale?.markers?.map(marker => <span key={marker.year} className="range-scale-marker" style={{ left: `${scale.position(marker.year)}%` }} aria-hidden="true">{marker.label}</span>)}
    </div>
    <div className="range-endpoints" aria-hidden="true">{endpoints.map(label => <span key={label}>{label}</span>)}</div>
    <div className="range-pan">
      <button type="button" aria-label={`Move range ${step} ${step === 1 ? "year" : "years"} earlier`} disabled={disabled || a === min} onClick={() => pan(-step)}>← Earlier</button>
      <div className="year-inputs" onBlur={event => { if (!ignoreBlur.current && !event.currentTarget.contains(event.relatedTarget)) commitFields(true); }}>
        <label><span>From</span><input ref={fromInput} aria-label={inputPrefix ? `${inputPrefix}start year` : "Start year"} type="number" step={1} defaultValue={start} min={minimum} max={maximum} disabled={disabled} aria-invalid={!!message} aria-describedby={message ? errorId : undefined} onKeyDown={fieldKey} onInput={() => setInvalid(null)} /></label>
        <label><span>To</span><input ref={toInput} aria-label={inputPrefix ? `${inputPrefix}end year` : "End year"} type="number" step={1} defaultValue={end} min={minimum} max={maximum} disabled={disabled} aria-invalid={!!message} aria-describedby={message ? errorId : undefined} onKeyDown={fieldKey} onInput={() => setInvalid(null)} /></label>
        {message && <p className="year-error" id={errorId} role="alert">{message}</p>}
      </div>
      <button type="button" aria-label={`Move range ${step} ${step === 1 ? "year" : "years"} later`} disabled={disabled || b === max} onClick={() => pan(step)}>Later →</button>
    </div>
  </section>;
}
