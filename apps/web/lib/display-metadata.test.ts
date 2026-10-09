import { expect, it } from "vitest";
import { artworkDate, displayMetadata, museumDescription } from "./display-metadata";
it.each([null, "", "Unknown", "Creation date not supplied by source", "Creator not recorded", "Dimensions not available", "In review", "No description added yet"])("omits placeholders: %s", value => expect(displayMetadata(value)).toBeUndefined());
it.each(["c. 1890–1892", "before 1760", "Attributed to Rembrandt", "Public domain Egypt", "Oil on canvas"])("preserves known or qualified information: %s", value => expect(displayMetadata(value)).toBe(value));
it("does not turn an unknown date into a date", () => { expect(artworkDate({ date_precision: "unknown", date_display: "Unverified date" })).toBeUndefined(); expect(artworkDate({ date_display: "1900" })).toBe("1900"); });
it("omits institution workflow notes, preserving museum descriptions", () => { expect(museumDescription("Museum authority candidate; source-backed reconciliation.")).toBeUndefined(); expect(museumDescription("A museum of Moroccan art in Rabat.")).toBe("A museum of Moroccan art in Rabat."); });
