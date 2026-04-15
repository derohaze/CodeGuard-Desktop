import { describe, expect, it } from "vitest";
import {
  builderStreamConfig,
  resolveStreamRevealBatchSize,
  resolveStreamingCharsPerSecond,
} from "./streaming";

describe("builder stream pacing", () => {
  it("starts revealing with a modest reserve buffer", () => {
    expect(builderStreamConfig.startBuffer).toBe(72);
    expect(builderStreamConfig.warmupMs).toBe(120);
  });

  it("keeps revealing streamed text in smaller batches while buffered content exists", () => {
    expect(resolveStreamRevealBatchSize(12, false, 0.1)).toBe(1);
    expect(resolveStreamRevealBatchSize(48, false, 0.2)).toBe(1);
    expect(resolveStreamRevealBatchSize(120, false, 0.3)).toBe(2);
  });

  it("flushes completed responses faster", () => {
    expect(resolveStreamRevealBatchSize(50, true, 0.5)).toBe(3);
    expect(resolveStreamRevealBatchSize(200, true, 0.5)).toBe(8);
  });

  it("slows live reveal when the buffer is getting thin", () => {
    expect(resolveStreamingCharsPerSecond(24)).toBeLessThan(resolveStreamingCharsPerSecond(120));
    expect(resolveStreamingCharsPerSecond(24)).toBeGreaterThanOrEqual(10);
    expect(resolveStreamingCharsPerSecond(240)).toBeGreaterThan(builderStreamConfig.streamingCharsPerSecond);
  });
});
