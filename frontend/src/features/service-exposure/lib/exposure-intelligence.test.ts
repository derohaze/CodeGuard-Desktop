import { describe, expect, it } from "vitest";
import { buildExposureHotspots, summarizeExposureHotspots } from "./exposure-intelligence";

describe("exposure intelligence", () => {
  const session = {
    session: {
      tracedPathsCount: 9,
      totalPathsCount: 12,
      graphSummary: {
        external_surfaces: ["REST API", "Webhook"],
        trust_boundaries: ["browser -> api", "api -> worker"],
      },
      repositoryGraph: {
        public_entrypoints: ["src/main.tsx", "src/routes.tsx"],
        service_boundaries: ["ui/api", "api/worker"],
        external_calls: ["auth provider"],
      },
      securityRegistry: {
        network_boundaries: ["http", "db"],
      },
      pathSummary: {
        dominant_path_type: "request-driven",
      },
    },
  };

  it("builds prioritized exposure hotspots", () => {
    const hotspots = buildExposureHotspots(session as never);

    expect(hotspots).toHaveLength(4);
    expect(hotspots[0].priority).toBe("critical");
    expect(hotspots.some((item) => item.hotspotClass === "boundary-drag")).toBe(true);
    expect(hotspots.some((item) => item.hotspotClass === "entrypoint-drag")).toBe(true);
  });

  it("summarizes exposure hotspot pressure", () => {
    const summary = summarizeExposureHotspots(buildExposureHotspots(session as never));

    expect(summary.hotspotCount).toBe(4);
    expect(summary.criticalHotspots).toBe(2);
    expect(summary.boundaryDrag).toBe(1);
    expect(summary.networkDrag).toBe(1);
    expect(summary.pathDrag).toBe(1);
    expect(summary.entrypointDrag).toBe(1);
    expect(summary.topHotspotLabel).toMatch(/critical/i);
  });
});
