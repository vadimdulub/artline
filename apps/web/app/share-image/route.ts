import { createElement as h } from "react";
import { ImageResponse } from "next/og";

// A self-contained brand card: no catalogue images, fonts or network requests.
export const dynamic = "force-static";

export function GET() {
  return new ImageResponse(
    h("div", { style: { display: "flex", flexDirection: "column", width: "100%", height: "100%", padding: "64px 80px", background: "#f2efe8", color: "#1b1916", fontFamily: "sans-serif" } },
      h("div", { style: { fontSize: 30, letterSpacing: 4, color: "#903f35" } }, "ARTLINE"),
      h("div", { style: { display: "flex", flexDirection: "column", marginTop: 42, fontSize: 72, lineHeight: 1.1, fontWeight: 700 } },
        h("span", null, "Art, literature & history."),
        h("span", null, "See the connections.")),
      h("div", { style: { marginTop: 30, fontSize: 28, color: "#625d55" } }, "Explore people, places and ideas through time."),
      h("div", { style: { display: "flex", flexDirection: "column", gap: 16, marginTop: 48 } },
        ...[{ width: "70%", background: "#903f35", marginLeft: 0 }, { width: "62%", background: "#53745b", marginLeft: 150 }, { width: "45%", background: "#625d55", marginLeft: 390 }].map((style, key) =>
          h("div", { key, style: { ...style, height: 8, borderRadius: 4 } })))),
    { width: 1200, height: 630 },
  );
}
