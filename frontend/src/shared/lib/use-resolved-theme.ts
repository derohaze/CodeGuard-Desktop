import { useSyncExternalStore } from "react";

/**
 * Resolves the active color scheme by reading the `data-theme` attribute on
 * <html> (set by the app shell from the runtime "system"/"light"/"dark"
 * setting). Components with inline theme-token overrides (e.g. the sidebar)
 * subscribe here so they re-render when the mode changes, instead of relying
 * on CSS alone.
 */
function subscribeToAppTheme(onChange: () => void): () => void {
  if (typeof window === "undefined" || typeof document === "undefined") return () => undefined;
  const root = document.documentElement;
  const observer = new MutationObserver(onChange);
  observer.observe(root, { attributes: true, attributeFilter: ["data-theme"] });
  return () => observer.disconnect();
}

function getCurrentAppTheme(): "light" | "dark" {
  if (typeof document !== "undefined" && document.documentElement.dataset.theme === "light") {
    return "light";
  }
  return "dark";
}

export function useResolvedTheme(): "light" | "dark" {
  return useSyncExternalStore(subscribeToAppTheme, getCurrentAppTheme, () => "dark");
}