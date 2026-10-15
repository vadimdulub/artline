import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { GuideDirectory } from "@/app/guides/GuideDirectory";
import type { GuideSearchEntry, GuideSearchPage } from "@/lib/guide-search";

vi.mock("@/components/museum-state", () => ({
  useCatalogueRequest: (_url: string, _retry: number, initial: GuideSearchPage) => ({ data: initial, loading: false, error: null }),
}));
vi.mock("@/lib/url-state", () => ({ useQueryString: (initial: string) => initial, updateQuery: vi.fn() }));
vi.mock("next/link", () => ({ default: ({ children, href }: { children: ReactNode; href: string }) => <a href={href}>{children}</a> }));

const base: GuideSearchEntry = { slug: "louvre", kind: "museum", href: "/guides/louvre", title: "Louvre: Masterpieces", label: "Louvre", location: "Paris, France", subtitle: "Twenty paintings", image: "", count: 20, languages: 10 };
function show(items: GuideSearchEntry[]) {
  render(<GuideDirectory initialQuery="" initialPage={{ items, total: items.length, matched: items.length, counts: { all: items.length, museum: items.filter(i => i.kind === "museum").length, artist: items.filter(i => i.kind === "artist").length, using: 0 }, next_cursor: "" }} />);
}

describe("guide directory naming", () => {
  it.each([
    "Louvre: Masterpieces", "Лувр: шедевры", "Louvre: capolavori", "Louvre: Meisterwerke", "卢浮宫：杰作",
    "Louvre : chefs-d’œuvre", "Louvre: obras maestras", "Louvre: obras-primas", "ルーヴル美術館：名作", "متحف اللوفر: روائع",
  ])("shows the museum guide title, not only its museum label: %s", title => {
    show([{ ...base, title }]);
    expect(screen.getByRole("heading", { level: 3, name: title })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 3, name: "Louvre" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: title })).toHaveAttribute("href", "/guides/louvre");
  });
  it("preserves artist labels and using-Artline labels", () => {
    show([
      { ...base, kind: "artist", slug: "frida-kahlo", href: "/guides/frida-kahlo", label: "Frida Kahlo", title: "Frida Kahlo: a different existing title" },
      { ...base, kind: "using", slug: "art-history-timeline", href: "/art-history-timeline", label: "Art history through time", title: "How to use the timeline" },
    ]);
    expect(screen.getByRole("heading", { level: 3, name: "Frida Kahlo" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 3, name: "Art history through time" })).toBeInTheDocument();
  });
});
