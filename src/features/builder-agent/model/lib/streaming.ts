const STREAM_REVEAL_START_BUFFER = 64;
const STREAM_REVEAL_WARMUP_MS = 180;
const STREAM_REVEAL_STREAMING_CPS = 52;
const STREAM_REVEAL_COMPLETION_CPS = 180;
const STREAM_REVEAL_TARGET_BUFFER = 96;

export const builderStreamConfig = {
  startBuffer: STREAM_REVEAL_START_BUFFER,
  warmupMs: STREAM_REVEAL_WARMUP_MS,
  streamingCharsPerSecond: STREAM_REVEAL_STREAMING_CPS,
  completionCharsPerSecond: STREAM_REVEAL_COMPLETION_CPS,
  targetBuffer: STREAM_REVEAL_TARGET_BUFFER,
};

export function splitStreamDisplayUnits(text: string): string[] {
  if (typeof Intl !== "undefined" && typeof Intl.Segmenter !== "undefined") {
    const segmenter = new Intl.Segmenter(undefined, { granularity: "grapheme" });
    return Array.from(segmenter.segment(text), (item) => item.segment);
  }
  return Array.from(text);
}

export function resolveStreamRevealBatchSize(
  bufferLength: number,
  sourceCompleted: boolean,
  revealBudget: number,
): number {
  if (bufferLength <= 0) {
    return 0;
  }

  if (!sourceCompleted && revealBudget < 1 && bufferLength < 10) {
    return 0;
  }

  if (sourceCompleted) {
    if (bufferLength > 240) return Math.max(10, Math.floor(revealBudget));
    if (bufferLength > 160) return Math.max(8, Math.floor(revealBudget));
    if (bufferLength > 96) return Math.max(5, Math.floor(revealBudget));
    if (bufferLength > 36) return Math.max(3, Math.floor(revealBudget));
    return Math.max(1, Math.floor(revealBudget));
  }

  if (bufferLength > 220) return Math.max(5, Math.floor(revealBudget));
  if (bufferLength > 140) return Math.max(4, Math.floor(revealBudget));
  if (bufferLength > 80) return Math.max(3, Math.floor(revealBudget));
  if (bufferLength > 32) return Math.max(2, Math.floor(revealBudget));
  return Math.max(1, Math.floor(revealBudget));
}

export function resolveStreamingCharsPerSecond(bufferLength: number): number {
  const normalized = Math.max(0.35, Math.min(1.6, bufferLength / STREAM_REVEAL_TARGET_BUFFER));
  return Math.max(24, Math.round(STREAM_REVEAL_STREAMING_CPS * normalized));
}
