import type { IncomingMessage, ServerResponse } from "node:http";

const ALLOWED_METHODS = "GET,POST,PATCH,DELETE,OPTIONS";
const ALLOWED_HEADERS = "Content-Type,Authorization";

export function applyCorsHeaders(
  request: IncomingMessage,
  response: ServerResponse,
  allowedOrigins: readonly string[],
): boolean {
  const origin = request.headers.origin;
  if (origin !== undefined) {
    if (!allowedOrigins.includes(origin)) {
      return false;
    }
    response.setHeader("Access-Control-Allow-Origin", origin);
    response.setHeader("Vary", "Origin");
  }

  response.setHeader("Access-Control-Allow-Methods", ALLOWED_METHODS);
  response.setHeader("Access-Control-Allow-Headers", ALLOWED_HEADERS);
  return true;
}
