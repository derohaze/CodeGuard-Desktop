export interface MockBuilderStreamPlan {
  reasoning: [string, string, string][];
  response: string;
}

const FINAL_RESPONSE_BANK = [
  "Here is the cleanest path: scope the change to the active workspace, update the smallest surface that fixes the issue, then verify the behavior before expanding anything else.",
  "I would approach this in three steps: inspect the current flow, apply one targeted change in the selected project, then run a quick regression pass on the affected path.",
  "The most practical next move is to keep the shell stable, isolate the change inside the current workspace, and avoid broad refactors until the behavior is verified.",
  "I can handle this by narrowing the request to one implementation slice, preserving the current UX, and leaving the backend integration seam ready for later.",
];

export function createMockBuilderStreamPlan(prompt: string): MockBuilderStreamPlan {
  const index = prompt.trim().length % FINAL_RESPONSE_BANK.length;

  return {
    reasoning: [
      [
        "Checking the current workspace shape",
        "I need to confirm how the active project is structured before I answer.",
        "I am analyzing the current UI and state boundaries for the safest entry point.",
      ],
      [
        "Narrowing the implementation path",
        "I am reducing the request to the smallest clean change that will actually hold up.",
        "I am comparing the current interaction flow with the builder-specific path.",
      ],
      [
        "Preparing the response",
        "I have enough context to turn this into one direct answer for the active chat.",
        "I am packaging the result so the next implementation step stays clear and focused.",
      ],
    ],
    response: FINAL_RESPONSE_BANK[index],
  };
}
