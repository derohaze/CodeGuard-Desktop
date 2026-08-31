import { useCallback, useState } from "react";
import {
  BUILDER_COMPOSER_SETTINGS_KEY,
  DEFAULT_BUILDER_COMPOSER_SETTINGS,
  type BuilderComposerSettings,
} from "../lib/types";

function loadComposerSettings(): BuilderComposerSettings {
  if (typeof window === "undefined") {
    return DEFAULT_BUILDER_COMPOSER_SETTINGS;
  }

  try {
    const stored = window.localStorage.getItem(BUILDER_COMPOSER_SETTINGS_KEY);
    if (!stored) {
      return DEFAULT_BUILDER_COMPOSER_SETTINGS;
    }
    const parsed = JSON.parse(stored) as Partial<BuilderComposerSettings>;
    return {
      permissionMode: parsed.permissionMode === "default" ? "default" : "full-access",
      planMode: Boolean(parsed.planMode),
      responseSpeed: parsed.responseSpeed === "speed" ? "speed" : "normal",
      attachedFiles: Array.isArray(parsed.attachedFiles) ? parsed.attachedFiles : [],
    };
  } catch {
    return DEFAULT_BUILDER_COMPOSER_SETTINGS;
  }
}

export function useBuilderComposerSettings() {
  const [composerSettings, setComposerSettings] = useState<BuilderComposerSettings>(() => loadComposerSettings());

  const persistComposerSettings = useCallback((nextSettings: BuilderComposerSettings) => {
    setComposerSettings(nextSettings);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(BUILDER_COMPOSER_SETTINGS_KEY, JSON.stringify(nextSettings));
    }
  }, []);

  return {
    composerSettings,
    persistComposerSettings,
  };
}
