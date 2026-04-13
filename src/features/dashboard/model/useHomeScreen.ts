import { useEffect, useMemo, useState } from "react";
import {
  inferWorkspace,
  RECENT_SOURCES_KEY,
  rememberRecentSource,
  type RecentSource,
  type SourceTargetType,
} from "./home-screen.utils";

const scanPresets = [
  {
    id: "safe",
    label: "Safe mode",
    description: "Strict checks with calmer defaults and fewer false positives.",
  },
  {
    id: "balanced",
    label: "Balanced",
    description: "Best default for most repositories and day-to-day review flows.",
  },
  {
    id: "aggressive",
    label: "Aggressive",
    description: "Broader heuristics to surface more risky paths early.",
  },
] as const;

export function useHomeScreen() {
  const canBrowse = typeof window !== "undefined" && typeof window.electronAPI?.pickPath === "function";
  const [preset, setPreset] = useState<(typeof scanPresets)[number]["id"]>("balanced");
  const [scanMode, setScanMode] = useState<"fast" | "deep">("deep");
  const [targetType, setTargetType] = useState<SourceTargetType>("folder");
  const [targetPath, setTargetPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [pickingPath, setPickingPath] = useState(false);
  const [recentSources, setRecentSources] = useState<RecentSource[]>([]);

  const selectedPreset = scanPresets.find((item) => item.id === preset) ?? scanPresets[1];
  const inferredWorkspace = useMemo(() => inferWorkspace(targetPath, targetType), [targetPath, targetType]);
  const selectedTargetName = useMemo(() => basenameFromPath(targetPath), [targetPath]);
  const scanSummary = useMemo(
    () =>
      scanMode === "deep"
        ? targetType === "folder"
          ? "Deep analysis will traverse the full folder scope, build repository graphs, trace source-to-sink paths, and push coverage toward full review."
          : "Deep analysis will fully traverse the selected file, segment it into review blocks, and follow nearby calls to build full path evidence."
        : targetType === "folder"
          ? "Fast analysis will focus on the highest-risk files and path units first for a quicker partial review."
          : "Fast analysis will review the selected file quickly, then inspect nearby hotspots for a fast first pass.",
    [scanMode, targetType],
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const stored = window.localStorage.getItem(RECENT_SOURCES_KEY);
      if (!stored) return;
      const parsed = JSON.parse(stored) as RecentSource[];
      if (Array.isArray(parsed)) {
        setRecentSources(parsed);
      }
    } catch {
      setRecentSources([]);
    }
  }, []);

  const persistRecentSources = (nextSources: RecentSource[]) => {
    setRecentSources(nextSources);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(RECENT_SOURCES_KEY, JSON.stringify(nextSources));
    }
  };

  const rememberSource = (path: string, type: SourceTargetType) => {
    persistRecentSources(rememberRecentSource(recentSources, path, type));
  };

  const visibleRecentSources = recentSources.filter((item) => item.type === targetType);

  const removeRecentSource = (path: string, type: SourceTargetType) => {
    persistRecentSources(recentSources.filter((item) => !(item.path === path && item.type === type)));
  };

  const clearRecentSources = (type: SourceTargetType) => {
    persistRecentSources(recentSources.filter((item) => item.type !== type));
  };

  const pickPath = async () => {
    if (!canBrowse || pickingPath) return;
    setPickingPath(true);
    try {
      const picked = await window.electronAPI?.pickPath?.(targetType);
      if (picked) {
        setTargetPath(picked);
        rememberSource(picked, targetType);
      }
    } finally {
      setPickingPath(false);
    }
  };

  return {
    canBrowse,
    clearRecentSources,
    inferredWorkspace,
    loading,
    pickPath,
    pickingPath,
    preset,
    recentSources: visibleRecentSources,
    removeRecentSource,
    scanMode,
    scanPresets,
    scanSummary,
    selectedPreset,
    selectedTargetName,
    setLoading,
    setPreset,
    setScanMode,
    setTargetPath,
    setTargetType,
    targetPath,
    targetType,
  };
}

function basenameFromPath(path: string) {
  if (!path) return "No source selected yet";
  const normalized = path.replace(/\\/g, "/");
  const parts = normalized.split("/");
  return parts[parts.length - 1] || normalized;
}
