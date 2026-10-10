type CookieReader = { get(name: string): { name: string; value: string } | undefined };

// Never forward editor credentials, OAuth state, or arbitrary client headers.
export function memberRequestHeaders(cookies: CookieReader): Headers {
  const headers = new Headers();
  const tokens = ["__Host-artline_session", "artline_session"].flatMap(name => {
    const cookie = cookies.get(name);
    return cookie && /^[A-Za-z0-9_-]{43}$/.test(cookie.value) ? [`${name}=${cookie.value}`] : [];
  });
  if (tokens.length) headers.set("cookie", tokens.join("; "));
  return headers;
}
