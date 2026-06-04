import http, { type IncomingMessage, type ServerResponse } from "node:http";
import { performance } from "node:perf_hooks";

import type { NodeIoConfig } from "../config.js";
import { applyCorsHeaders } from "../http/cors.js";
import { sendJson } from "../http/json.js";
import { logRequest } from "../logger.js";
import { healthResponse, isHealthRoute } from "../routes/health.js";
import { isRuntimeRoute, runtimeResponse } from "../routes/runtime.js";

export function createNodeIoServer(config: NodeIoConfig): http.Server {
  const server = http.createServer((request, response) => {
    handleRequest(config, request, response);
  });

  server.requestTimeout = config.requestTimeoutMs;
  server.headersTimeout = Math.min(60_000, config.requestTimeoutMs);
  return server;
}

function handleRequest(config: NodeIoConfig, request: IncomingMessage, response: ServerResponse): void {
  const startedAt = performance.now();
  response.on("finish", () => logAccess(request, response, startedAt));

  if (!applyCorsHeaders(request, response, config.corsAllowedOrigins)) {
    sendJson(response, 403, { detail: "CORS origin is not allowed." });
    return;
  }

  if (request.method === "OPTIONS") {
    response.writeHead(204);
    response.end();
    return;
  }

  const requestUrl = parseRequestUrl(config, request);
  if (requestUrl === null) {
    sendJson(response, 400, { detail: "Invalid request URL." });
    return;
  }

  const method = request.method ?? "GET";
  if (isHealthRoute(method, requestUrl.pathname)) {
    sendJson(response, 200, healthResponse());
    return;
  }

  if (isRuntimeRoute(method, requestUrl.pathname)) {
    sendJson(response, 200, runtimeResponse());
    return;
  }

  sendJson(response, 404, { detail: "Route not found." });
}

function parseRequestUrl(config: NodeIoConfig, request: IncomingMessage): URL | null {
  try {
    return new URL(request.url ?? "/", `http://${request.headers.host ?? `${config.host}:${config.port}`}`);
  } catch {
    return null;
  }
}

function logAccess(
  request: IncomingMessage,
  response: ServerResponse,
  startedAt: number,
): void {
  logRequest({
    method: request.method ?? "GET",
    path: request.url ?? "/",
    statusCode: response.statusCode,
    durationMs: performance.now() - startedAt,
    target: "node-io",
  });
}
