export type PermissionMode = "default" | "full-access";
export type ResponseSpeed = "normal" | "speed";

export interface BuilderComposerSettings {
  permissionMode: PermissionMode;
  planMode: boolean;
  responseSpeed: ResponseSpeed;
  attachedFiles: string[];
}

export const DEFAULT_BUILDER_COMPOSER_SETTINGS: BuilderComposerSettings = {
  permissionMode: "full-access",
  planMode: false,
  responseSpeed: "normal",
  attachedFiles: [],
};

export const BUILDER_COMPOSER_SETTINGS_KEY = "builder-composer-settings";
