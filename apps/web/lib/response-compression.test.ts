import { describe, expect, it } from "vitest";
import { acceptsGzip } from "./response-compression";
describe("catalogue response compression negotiation", () => {
  it.each(["gzip", "br, gzip;q=0.5", "GZIP", "*;q=1"])("accepts %s", header => expect(acceptsGzip(header)).toBe(true));
  it.each([null, "", "br", "gzip;q=0", "gzip;q=0, *;q=1", "gzip;q=invalid", "gzip;q=2"])("does not encode against %s", header => expect(acceptsGzip(header)).toBe(false));
});
