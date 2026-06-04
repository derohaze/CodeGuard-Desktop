export function isRuntimeRoute(method: string, path: string): boolean {
  return method === "GET" && path === "/api/v1/node/runtime";
}

export function runtimeResponse(): Record<string, unknown> {
  return {
    service: "node-io",
    role: "local-runtime-io",
    pid: process.pid,
    uptime_seconds: Math.round(process.uptime()),
    node_version: process.version,
    platform: process.platform,
    arch: process.arch,
  };
}
