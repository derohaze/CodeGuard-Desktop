import { motion } from "framer-motion";
import type { ReactNode } from "react";
import {
  ArrowLeft01Icon,
  BalanceScaleIcon,
  Settings01Icon,
  Shield01Icon,
  ZapIcon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import type { RuntimeSettings, UpdateRuntimeSettingsPayload } from "@/shared/api/security";

interface SettingsScreenProps {
  onBack: () => void;
  settings: RuntimeSettings;
  isSaving: boolean;
  onPatchSettings: (patch: UpdateRuntimeSettingsPayload) => void | Promise<void>;
  isSidebarCollapsed?: boolean;
}

const sections = [{ id: "general", label: "General", icon: Settings01Icon }];

const scanModes = [
  { value: "deep", label: "Deep analysis" },
  { value: "fast", label: "Fast analysis" },
] as const;
const scanPresets = [
  {
    id: "safe",
    label: "Safe mode",
    description: "Prioritize high-confidence findings and calmer defaults for steady review flows.",
    icon: Shield01Icon,
    defaultMode: "deep",
  },
  {
    id: "balanced",
    label: "Balanced",
    description: "Keep security coverage broad without turning every analyst run into a noisy sweep.",
    icon: BalanceScaleIcon,
    defaultMode: "deep",
  },
  {
    id: "aggressive",
    label: "Aggressive",
    description: "Push deeper heuristics and stricter checks to surface more risky edges earlier.",
    icon: ZapIcon,
    defaultMode: "fast",
  },
] as const;

const remediationAttemptOptions = [1, 2, 3, 4, 5];
const ingestionRpsOptions = [2, 5, 10, 15, 20, 30];
const ingestionRetryOptions = [1, 2, 3, 4, 5, 6];

export function SettingsScreen({ onBack, settings, onPatchSettings, isSaving, isSidebarCollapsed = false }: SettingsScreenProps) {
  return (
    <div key="settings-screen" className="flex min-h-0 flex-1 overflow-hidden bg-[#171717]">
      {/* Left nav — collapsible like workspace sidebar, Codex warm dark */}
      <div
        className="relative shrink-0 overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]"
        style={{ width: isSidebarCollapsed ? 0 : 240 }}
        aria-hidden={isSidebarCollapsed}
      >
        <motion.aside
          className="absolute inset-y-0 left-0 flex w-[240px] min-h-0 flex-col overflow-hidden bg-[#171717]"
          initial={false}
          animate={{ x: isSidebarCollapsed ? -240 : 0, opacity: isSidebarCollapsed ? 0 : 1 }}
          transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
        >
          <div className="flex h-[44px] items-center border-b border-white/[0.06] px-3">
            <button
              onClick={onBack}
              className="app-no-drag inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[12.5px] font-normal text-white/60 transition-colors hover:bg-white/[0.06] hover:text-white/85"
            >
              <HugeiconsIcon icon={ArrowLeft01Icon} size={14} strokeWidth={1.7} color="currentColor" />
              <span>Back to app</span>
            </button>
          </div>

          <div className="space-y-0.5 px-2 py-3">
            {sections.map((section) => {
              return (
                <button
                  key={section.id}
                  className="flex w-full items-center gap-2 rounded-lg bg-white/[0.08] px-2.5 py-1.5 text-left text-[12.5px] font-medium text-white"
                >
                  <HugeiconsIcon icon={section.icon} size={14} strokeWidth={1.7} color="currentColor" className="text-white/70" />
                  <span>{section.label}</span>
                </button>
              );
            })}
          </div>
        </motion.aside>
      </div>

      {/* Right content — Codex #121212 / card #1e1e1e with page curve like external app (outer page curve) */}
      <div
        className={`flex min-h-0 flex-1 flex-col overflow-hidden bg-[#171717] transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)] ${
          isSidebarCollapsed ? "rounded-t-[16px]" : "rounded-tl-[16px]"
        }`}
      >
        <div className="hide-scrollbar flex min-h-0 flex-1 flex-col overflow-y-auto bg-[#121212]">
          <div className="mx-auto flex w-full max-w-[860px] flex-col gap-5 px-8 py-7">
          <div className="flex items-center justify-between gap-6">
            <div>
              <h2 className="text-[22px] font-semibold tracking-[-0.02em] text-white">General</h2>
              {isSaving ? <p className="mt-1 text-[11px] text-white/40">Saving settings…</p> : null}
            </div>
          </div>

          <div className="overflow-hidden rounded-[16px] border border-white/[0.06] bg-[#1e1e1e]">
            {/* Analyst preset — Codex card style */}
            <div className="border-b border-white/[0.06] px-4 py-4">
              <div className="mb-3">
                <p className="text-[13px] font-medium text-white">Analyst preset</p>
                <p className="mt-1 text-[12.5px] leading-5 text-white/55">Choose the default posture for new analysis sessions.</p>
              </div>

              <div className="grid gap-2.5 md:grid-cols-3">
                {scanPresets.map((preset) => {
                  const active = settings.defaultPreset === preset.id;
                  return (
                    <button
                      key={preset.id}
                      onClick={() => {
                        void onPatchSettings({
                          defaultPreset: preset.id,
                          defaultScanMode: preset.defaultMode,
                        });
                      }}
                      className={`group rounded-xl border px-3.5 py-3.5 text-left transition-all ${
                        active
                          ? "bg-[#2a241e] border-[#c9a86a]/25 shadow-[0_0_0_1px_rgba(201,168,106,0.12)]"
                          : "bg-[#232323] border-white/[0.06] hover:bg-[#262626] hover:border-white/[0.08]"
                      }`}
                    >
                      <div className="flex items-center gap-2 text-white">
                        <div
                          className={`flex h-7 w-7 items-center justify-center rounded-lg ${
                            active ? "bg-white/[0.08] text-white" : "bg-white/[0.06] text-white/70"
                          }`}
                        >
                          <HugeiconsIcon icon={preset.icon} size={13} strokeWidth={1.7} color="currentColor" />
                        </div>
                        <span className="text-[12.5px] font-medium">{preset.label}</span>
                      </div>
                      <p className="mt-2.5 text-[12px] leading-5 text-white/55">{preset.description}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            <SettingsRow
              title="Default analysis mode"
              description="Set how new security analysis sessions start."
              control={
                <Select
                  value={settings.defaultScanMode}
                  onValueChange={(value) => void onPatchSettings({ defaultScanMode: value as RuntimeSettings["defaultScanMode"] })}
                >
                  <SelectTrigger className={selectClassName}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className={selectContentClassName}>
                    {scanModes.map((mode) => (
                      <SelectItem key={mode.value} value={mode.value} className={selectItemClassName}>
                        {mode.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              }
            />

            <SettingsRow
              title="Auto-open results"
              description="Open findings automatically after analysis completion."
              control={
                <Switch
                  checked={settings.autoOpenResults}
                  onCheckedChange={(checked) => void onPatchSettings({ autoOpenResults: checked })}
                />
              }
            />

            <SettingsRow
              title="Sidebar behavior"
              description="Remember the last open or collapsed state."
              control={
                <Switch
                  checked={settings.rememberSidebarState}
                  onCheckedChange={(checked) => void onPatchSettings({ rememberSidebarState: checked })}
                />
              }
            />

            <SettingsRow
              title="Remediation retries"
              description="Maximum tuning attempts per remediation run."
              control={
                <Select
                  value={String(settings.remediationMaxAttempts)}
                  onValueChange={(value) => void onPatchSettings({ remediationMaxAttempts: Number(value) })}
                >
                  <SelectTrigger className={selectClassName}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className={selectContentClassName}>
                    {remediationAttemptOptions.map((value) => (
                      <SelectItem key={value} value={String(value)} className={selectItemClassName}>
                        {value}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              }
            />

            <SettingsRow
              title="Reuse explanation on retry"
              description="Reduce provider requests by reusing the first explanation across retries."
              control={
                <Switch
                  checked={settings.remediationReuseExplanation}
                  onCheckedChange={(checked) => void onPatchSettings({ remediationReuseExplanation: checked })}
                />
              }
            />

            <SettingsRow
              title="External ingestion max RPS"
              description="Rate limit for external security knowledge fetch runs."
              control={
                <Select
                  value={String(settings.externalIngestionMaxRps)}
                  onValueChange={(value) => void onPatchSettings({ externalIngestionMaxRps: Number(value) })}
                >
                  <SelectTrigger className={selectClassName}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className={selectContentClassName}>
                    {ingestionRpsOptions.map((value) => (
                      <SelectItem key={value} value={String(value)} className={selectItemClassName}>
                        {value} req/s
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              }
            />

            <SettingsRow
              title="External ingestion retries"
              description="Retry attempts for transient external source failures."
              control={
                <Select
                  value={String(settings.externalIngestionRetryAttempts)}
                  onValueChange={(value) => void onPatchSettings({ externalIngestionRetryAttempts: Number(value) })}
                >
                  <SelectTrigger className={selectClassName}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className={selectContentClassName}>
                    {ingestionRetryOptions.map((value) => (
                      <SelectItem key={value} value={String(value)} className={selectItemClassName}>
                        {value}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              }
              border={false}
            />
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}

function SettingsRow({
  title,
  description,
  control,
  border = true,
}: {
  title: string;
  description: string;
  control: ReactNode;
  border?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between gap-6 px-4 py-3.5 ${border ? "border-b border-white/[0.06]" : ""}`}
    >
      <div className="min-w-0 pr-4">
        <p className="text-[13px] font-medium leading-none text-white">{title}</p>
        <p className="mt-1.5 text-[12.5px] leading-5 text-white/55">{description}</p>
      </div>
      <div className="shrink-0">{control}</div>
    </div>
  );
}

const selectClassName =
  "h-8 w-[152px] rounded-lg border border-white/10 bg-[#2a2a2a] text-[12.5px] font-medium text-white hover:bg-[#303030] focus:ring-0 focus:ring-offset-0 data-[placeholder]:text-white/60";

const selectContentClassName =
  "rounded-xl border border-white/10 bg-[#232323] text-white shadow-[0_16px_32px_rgba(0,0,0,0.5)]";

const selectItemClassName = "rounded-md text-[12.5px] focus:bg-white/[0.06] focus:text-white";
