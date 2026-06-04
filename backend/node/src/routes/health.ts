const HEALTH_PATHS = new Set(["/health", "/api/v1/node/health"]);

export function isHealthRoute(method: string, path: string): boolean {
  return method === "GET" && HEALTH_PATHS.has(path);
}

export function healthResponse(): Record<string, unknown> {
  return {
    status: "ok",
    service: "node-io",
    role: "local-runtime-io",
    owned_surfaces: ["runtime-health", "process-metadata"],
  };
}
