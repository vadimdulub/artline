"use client";
import { MultiSelectFilter } from "./MultiSelectFilter";
import { usePainterChoices } from "./use-painter-choices";
import { MapPickerFrame, isMapPickerControl } from "./MapPickerFrame";

export function MapPainterPicker({ values, onChange }: { values: string[]; onChange: (values: string[]) => void }) {
  const choices = usePainterChoices(values);
  return <MapPickerFrame name="Painters" className="map-painter-picker"><MultiSelectFilter label="Painters" allLabel="Choose painters" values={values} onChange={onChange}
    options={choices.options} remote={choices.remote} unavailable={choices.unavailable} retry={choices.retry} keepOpenOnClick={isMapPickerControl} helpText="" /></MapPickerFrame>;
}
