import { createServer } from "node:http";
import { directoryResponse } from "./responsive-api-fixture.cjs";

createServer((request, response) => {
  const body = request.method === "GET" ? directoryResponse(new URL(request.url, "http://127.0.0.1")) : undefined;
  response.writeHead(request.method !== "GET" ? 405 : body === undefined ? 404 : 200, { "Content-Type": "application/json" });
  response.end(JSON.stringify(body ?? { error: { message: "Outside the responsive fixture" } }));
}).listen(3098, "127.0.0.1");
