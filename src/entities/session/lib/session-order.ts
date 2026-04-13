import type { Session } from "@/entities/session/model/types";

export function mergeSessionOrder(currentOrder: string[], nextSessions: Session[]): string[] {
  const nextIds = nextSessions.map((session) => session.id);
  const retained = currentOrder.filter((id) => nextIds.includes(id));
  const newSessionIds = nextIds.filter((id) => !retained.includes(id));
  return [...newSessionIds, ...retained];
}
