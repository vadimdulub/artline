import type { Paragraph, PhrasingContent, Root, RootContent } from "mdast";

// Presentation only: the stored source and editorial records remain unchanged.
export function cleanEditorialBiography(text: string) {
  return text.replace(/Short authority description; full biography awaits editorial review\./g, "").trim();
}
const segmenter = new Intl.Segmenter("en", { granularity: "sentence" });
function paragraphBreaks(text: string): number[] {
  if (text.trim().split(/\s+/).length <= 120) return [];
  const breaks: number[] = [];
  let start = 0;
  for (const sentence of segmenter.segment(text)) {
    const end = sentence.index + sentence.segment.length;
    // Keep initials and common abbreviated titles attached to the following name.
    if (/(?:\b(?:Mr|Mrs|Ms|Dr|Prof|St|Jr|Sr|c|ca|vs)|\b[A-Z])\.$/.test(sentence.segment.trim())) continue;
    if (text.slice(start, end).trim().split(/\s+/).length < 65 || text.slice(end).trim().split(/\s+/).length < 25) continue;
    breaks.push(end); start = end;
  }
  return breaks;
}
export function referenceParagraphs(text: string): string[] {
  return text.split(/\r?\n+/).flatMap(paragraph => {
    const cuts = [0, ...paragraphBreaks(paragraph), paragraph.length];
    return cuts.slice(1).map((end, index) => paragraph.slice(cuts[index], end).trim()).filter(Boolean);
  });
}
function inlineText(node: PhrasingContent): string {
  if ("value" in node) return node.value;
  if ("children" in node) return node.children.map(inlineText).join("");
  return "";
}
// Split long prose without cutting an emphasis span, link, code fragment or list.
// Markdown structure stays in the AST; only plain-text sentence boundaries move.
export function remarkBiographyParagraphs() {
  return (tree: Root) => {
    tree.children = tree.children.flatMap<RootContent>(node => {
      if (node.type !== "paragraph") return [node];
      const text = node.children.map(inlineText).join("");
      const cuts = paragraphBreaks(text);
      if (!cuts.length) return [node];
      const result: Paragraph[] = [];
      let children: PhrasingContent[] = [], offset = 0;
      for (const child of node.children) {
        const length = inlineText(child).length;
        if (child.type === "text") {
          let local = 0;
          for (const cut of cuts.filter(cut => cut > offset && cut <= offset + length)) {
            children.push({ type: "text", value: child.value.slice(local, cut - offset).trimEnd() });
            result.push({ type: "paragraph", children }); children = []; local = cut - offset;
          }
          if (local < length) children.push({ ...child, value: child.value.slice(local) });
        } else children.push(child);
        offset += length;
      }
      if (children.length) result.push({ type: "paragraph", children });
      return result;
    });
  };
}
