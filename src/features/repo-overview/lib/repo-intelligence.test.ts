import { describe, expect, it } from "vitest";
import { buildRepoHotspots, summarizeRepoHotspots } from "./repo-intelligence";

describe("repo intelligence", () => {
  const session = {
    session: {
      coveragePercent: 82,
      skippedFilesCount: 3,
      segmentationSummary: {
        identity_surfaces: ["login", "session", "admin"],
      },
      securityRegistry: {
        auth_components: ["session"],
        data_sinks: ["database", "filesystem"],
        user_inputs: ["forms", "query", "headers"],
        network_boundaries: ["http"],
      },
      graphSummary: {
        external_surfaces: ["REST API", "webhook"],
        trust_boundaries: ["browser -> api", "api -> worker"],
      },
    },
  };

  it("builds prioritized repository hotspots", () => {
    const hotspots = buildRepoHotspots(session as never);

    expect(hotspots).toHaveLength(4);
    expect(hotspots[0].hotspotClass).toBe("exposure-zone");
    expect(hotspots[0].priority).toBe("critical");
    expect(hotspots.some((item) => item.hotspotClass === "identity-zone")).toBe(true);
    expect(hotspots.some((item) => item.hotspotClass === "coverage-zone")).toBe(true);
  });

  it("summarizes repository hotspot pressure", () => {
    const summary = summarizeRepoHotspots(buildRepoHotspots(session as never));

    expect(summary.hotspotCount).toBe(4);
    expect(summary.criticalHotspots).toBe(2);
    expect(summary.identityZones).toBe(1);
    expect(summary.exposureZones).toBe(1);
    expect(summary.dataZones).toBe(1);
    expect(summary.coverageZones).toBe(1);
    expect(summary.topHotspotLabel).toMatch(/critical/i);
    expect(summary.topHotspotLabel).toMatch(/(exposure boundaries|identity surfaces)/i);
  });
});
