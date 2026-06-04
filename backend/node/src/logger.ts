const RESET = "\x1b[0m";
const DIM = "\x1b[2m";
const GREEN = "\x1b[32m";
const YELLOW = "\x1b[33m";
const RED = "\x1b[31m";
const MAGENTA = "\x1b[35m";
const CYAN = "\x1b[36m";

export function logStartup(message: string): void {
  console.log(`${MAGENTA}[node-io]${RESET} ${message}`);
}

export function logRequest(params: {
  method: string;
  path: string;
  statusCode: number;
  durationMs: number;
  target: "node-io";
}): void {
  const status = colorStatus(params.statusCode);
  console.log(
    `${MAGENTA}[node-io]${RESET} ${params.method.padEnd(6)} ${params.path} ` +
      `${status} ${DIM}${params.durationMs.toFixed(1)}ms${RESET} -> ${MAGENTA}${params.target}${RESET}`,
  );
}

function colorStatus(statusCode: number): string {
  if (statusCode >= 500) return `${RED}${statusCode}${RESET}`;
  if (statusCode >= 400) return `${YELLOW}${statusCode}${RESET}`;
  if (statusCode >= 300) return `${CYAN}${statusCode}${RESET}`;
  return `${GREEN}${statusCode}${RESET}`;
}
