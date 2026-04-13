export const taskLines = [
  { text: "Tracing attacker-controlled input through webhook delivery", type: "done" as const },
  { text: "Finagling...", type: "status" as const },
  { text: "Validating where shell execution crosses trust boundaries", type: "done" as const },
  { text: "Thinking...", type: "status" as const },
  { text: "Comparing safer subprocess invocation patterns", type: "done" as const },
  { text: "Now I'll implement the fix", type: "done" as const },
  { text: "Noodling...", type: "status" as const },
  { text: "Preparing patch summary and commit-ready output", type: "done" as const },
];

export const scanLiveLines = [
  "Analyzing repository structure...",
  "Mapping data flows across public endpoints...",
  "Detecting injection points in untrusted inputs...",
  "Reviewing authentication and session boundaries...",
  "Correlating findings with risky code paths...",
  "Preparing security summary and suggested fixes...",
];

export const dashboardMetrics = {
  securityScore: 72,
  issues: {
    critical: 3,
    high: 1,
    medium: 0,
    low: 0,
  },
};
