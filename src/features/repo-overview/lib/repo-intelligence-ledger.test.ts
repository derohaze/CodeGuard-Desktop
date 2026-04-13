import { describe, expect, it } from "vitest";
import { buildRepoIntelligenceLedger, summarizeRepoIntelligenceLedger } from "./repo-intelligence-ledger";

describe("repo intelligence ledger", () => {
  it("summarizes framework, registry, and coverage pressure", () => {
    const session = buildSession();
    const items = buildRepoIntelligenceLedger(session as never);
    const summary = summarizeRepoIntelligenceLedger(items);

    expect(summary.itemCount).toBeGreaterThan(0);
    expect(summary.frameworkItems).toBe(1);
    expect(summary.registryItems).toBe(1);
    expect(summary.coverageItems).toBe(1);
  });
});

function buildSession() {
  return {
    session: {
      repositoryInventory: { file_count: 42 },
      frameworkProfile: {
        languages: ["TypeScript", "Python"],
        runtimes: ["Node.js"],
        package_managers: ["bun"],
      },
      graphSummary: {
        services: ["api"],
        trust_boundaries: ["browser -> api"],
        external_surfaces: ["REST API"],
      },
      segmentationSummary: {
        critical_zones: ["auth"],
        sensitive_files: ["src/shared/api/security.ts"],
        identity_surfaces: ["login"],
        config_surfaces: ["vite.config.ts"],
      },
      securityRegistry: {
        auth_components: ["session"],
        data_sinks: ["database"],
        user_inputs: ["forms"],
        network_boundaries: ["http"],
      },
      coveragePercent: 80,
      skippedFilesCount: 3,
    },
  };
}
