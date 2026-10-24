import type { ReactNode } from "react";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { AddStudyRecords } from "./AddStudyRecords";
import { studyRequest } from "@/lib/studies";
vi.mock("@/lib/studies", async importOriginal => ({ ...await importOriginal<typeof import("@/lib/studies")>(), studyRequest: vi.fn() }));
vi.mock("./StudyDialog", () => ({ StudyDialog: ({ children }: { children: ReactNode }) => <section>{children}</section> }));
vi.mock("@/components/MemberNavigation", () => ({ NavigationIcon: () => null }));
beforeEach(() => { vi.useFakeTimers(); vi.mocked(studyRequest).mockResolvedValue({ items: [], next_cursor: "" }); });
afterEach(() => { cleanup(); vi.useRealTimers(); vi.clearAllMocks(); });
async function requestQuery() {
 await act(async () => { await vi.advanceTimersByTimeAsync(300); });
 return new URL(vi.mocked(studyRequest).mock.lastCall![0] as string, "https://artlines.org").searchParams;
}
it("starts artwork searches with pictures and preserves an explicit opt-out", async () => {
 render(<AddStudyRecords studyId="study" existing={[]} close={() => {}} added={() => {}} />);
 expect(screen.getByRole("checkbox", { name: "With images" })).toBeChecked();
 expect((await requestQuery()).get("image")).toBe("true");
 fireEvent.click(screen.getByRole("checkbox", { name: "With images" }));
 expect((await requestQuery()).get("image")).toBe("false");
 fireEvent.click(screen.getByRole("button", { name: "Reset filters" }));
 expect(screen.getByRole("checkbox", { name: "With images" })).toBeChecked();
 expect((await requestQuery()).get("image")).toBe("true");
});
it("applies the picture default only to artwork searches", async () => {
 render(<AddStudyRecords studyId="study" existing={[]} close={() => {}} added={() => {}} />);
 fireEvent.change(screen.getByRole("combobox", { name: "Record type" }), { target: { value: "book" } });
 expect((await requestQuery()).has("image")).toBe(false);
 expect(screen.queryByRole("checkbox", { name: "With images" })).toBeNull();
});
