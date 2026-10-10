const slug = "[a-z0-9]+(?:[-_][a-z0-9]+)*";
const destinationPath = new RegExp(`^(?:/artists/(${slug})(?:/works/[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12})?|/museums(?:/(${slug}))?)$`);

// OAuth destinations must stay on the selected, bounded catalogue route.
export function memberReturnTo(value: unknown): string | null {
  if (typeof value !== "string" || value.length > 768 || /[\\]|[^\x21-\x7e]/.test(value)) return null;
  const path = value.split(/[?#]/, 1)[0];
  if (["/", "/artists", "/artworks", "/all", "/bookmarks"].includes(path)) return value;
  const match = destinationPath.exec(path);
  return match && (!match[1] || match[1].length <= 100) && (!match[2] || match[2].length <= 100) ? value : null;
}

export function requiresMember(path: string): boolean {
  const pathname = path.split(/[?#]/, 1)[0];
  return pathname === "/bookmarks" || pathname === "/museums" || pathname.startsWith("/museums/");
}

export function memberSignInPath(destination: string): string {
  const returnTo = memberReturnTo(destination);
  return returnTo ? `/account?${new URLSearchParams({ return_to: returnTo })}` : "/account";
}

export function museumRecordPath(slug: string | null, query: Record<string, string | string[] | undefined>): string {
  const path = `/museums${slug ? `/${encodeURIComponent(slug)}` : ""}`;
  const filters = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (["catalogue", "preview", "status"].includes(key)) continue;
    for (const item of Array.isArray(value) ? value : value === undefined ? [] : [value]) filters.append(key, item);
  }
  return memberReturnTo(`${path}${filters.size ? `?${filters}` : ""}`) ?? memberReturnTo(path) ?? "/museums";
}
