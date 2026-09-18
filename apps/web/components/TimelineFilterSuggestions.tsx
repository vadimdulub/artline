import type { ReactNode } from "react";

export function TimelineFilterSuggestions<T extends { key: string; value: string; name: string; count: number }>({ suggestions, noun, needsFilter, disabled, guidanceId, onApply, onChooseFilters, children }: {
  suggestions: T[]; noun: "painters" | "books" | "authors" | "events"; needsFilter: boolean; disabled: boolean; guidanceId: string;
  onApply: (suggestion: T) => void; onChooseFilters: () => void; children?: ReactNode;
}) {
  return <div className="density-help">
    <p id={guidanceId}>{needsFilter ? `Many ${noun} overlap these years. Try a suggested filter to narrow the view, or choose your own above.` : `Choose a period to explore its ${noun}, or try a suggested filter. Each count matches the view you will open.`}</p>
    <div className="density-actions">
      {suggestions.map(suggestion => <button key={`${suggestion.key}-${suggestion.value}`} type="button" disabled={disabled} onClick={() => onApply(suggestion)} aria-label={`Filter by ${suggestion.name}, ${suggestion.count} ${noun}`}>{suggestion.name} · {suggestion.count}</button>)}
      {suggestions.length === 0 && <button type="button" disabled={disabled} onClick={onChooseFilters}>Choose filters</button>}
      {children}
    </div>
  </div>;
}
