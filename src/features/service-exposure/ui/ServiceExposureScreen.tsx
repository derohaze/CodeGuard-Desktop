import { motion } from "framer-motion";
import { Globe, Route, ShieldAlert, Waypoints } from "lucide-react";
import { buildExposureHotspots, summarizeExposureHotspots } from "@/features/service-exposure/lib/exposure-intelligence";
import type {
  ScanSessionDetail,
  WorkflowServiceExposureItem,
  WorkflowServiceExposureSummary,
} from "@/shared/api/security";

interface Props {
  session: ScanSessionDetail | null;
  serviceSummary?: WorkflowServiceExposureSummary | null;
  serviceExposureFeed?: WorkflowServiceExposureItem[] | null;
  onBack: () => void;
}

export function ServiceExposureScreen({
  session,
  serviceSummary = null,
  serviceExposureFeed = null,
  onBack,
}: Props) {
  if (!session) return null;

  const graph = session.session.graphSummary;
  const repositoryGraph = session.session.repositoryGraph;
  const registry = session.session.securityRegistry;
  const pathSummary = session.session.pathSummary;
  const hotspots = buildExposureHotspots(session);
  const localHotspotSummary = summarizeExposureHotspots(hotspots);
  const hotspotSummary = serviceSummary
    ? {
        hotspotCount: serviceSummary.hotspotCount,
        criticalHotspots: serviceSummary.criticalHotspots,
        boundaryDrag: serviceSummary.boundaryDrag,
        networkDrag: serviceSummary.networkDrag,
        pathDrag: serviceSummary.pathDrag,
        entrypointDrag: serviceSummary.entrypointDrag,
        topHotspotLabel: serviceSummary.topHotspotLabel,
      }
    : localHotspotSummary;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="hide-scrollbar flex-1 overflow-y-auto dotted-bg px-8 py-8"
    >
      <div className="mx-auto max-w-5xl space-y-4">
        <section
          className="rounded-2xl border bg-card px-5 py-5 shadow-card"
          style={{ borderColor: "hsl(var(--border-soft))" }}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-txt-tertiary">Service exposure view</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-txt-primary">{session.session.repo}</h2>
              <p className="mt-2 text-sm leading-6 text-txt-secondary">
                This surface summarizes trust boundaries, external surfaces, network boundaries, and traced path pressure for the active repository run.
              </p>
            </div>
            <span className="rounded-full bg-[#f4efe7] px-3 py-1 text-[11px] font-medium uppercase tracking-[0.14em] text-txt-secondary">
              {session.session.tracedPathsCount} traced path{session.session.tracedPathsCount === 1 ? "" : "s"}
            </span>
          </div>
        </section>

        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <ExposureCard
            icon={Globe}
            label="External surfaces"
            value={formatUnknown(graph?.external_surfaces)}
            note="Derived from current graph summary."
          />
          <ExposureCard
            icon={ShieldAlert}
            label="Trust boundaries"
            value={formatUnknown(graph?.trust_boundaries)}
            note="Repository trust boundaries currently captured in the scan."
          />
          <ExposureCard
            icon={Waypoints}
            label="Network boundaries"
            value={formatUnknown(registry?.network_boundaries)}
            note="Network boundary signals from the security registry."
          />
          <ExposureCard
            icon={Route}
            label="Path pressure"
            value={`${session.session.tracedPathsCount}/${session.session.totalPathsCount || session.session.tracedPathsCount}`}
            note={pathSummary ? formatUnknown(pathSummary) : "Path summary not captured."}
          />
        </section>

        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <ExposureCard
            icon={ShieldAlert}
            label="Exposure hotspots"
            value={`${hotspotSummary.hotspotCount} hotspot(s)`}
            note={hotspotSummary.topHotspotLabel}
          />
          <ExposureCard
            icon={Globe}
            label="Critical exposure"
            value={`${hotspotSummary.criticalHotspots} hotspot(s)`}
            note={`${hotspotSummary.boundaryDrag} boundary / ${hotspotSummary.entrypointDrag} entrypoint`}
          />
          <ExposureCard
            icon={Waypoints}
            label="Network drag"
            value={`${hotspotSummary.networkDrag} hotspot(s)`}
            note="Network and external-call pressure derived from registry and graph data."
          />
          <ExposureCard
            icon={Route}
            label="Path drag"
            value={`${hotspotSummary.pathDrag} hotspot(s)`}
            note="Path concentration still contributes to exposure pressure."
          />
        </section>

        <section className="grid gap-4 xl:grid-cols-2">
          <ExposureTable
            title="Repository exposure graph"
            rows={buildRows(repositoryGraph, [
              ["public_entrypoints", "Public entrypoints"],
              ["service_boundaries", "Service boundaries"],
              ["external_calls", "External calls"],
              ["data_flows", "Data flows"],
            ])}
          />
          <ExposureTable
            title="Security registry exposure"
            rows={buildRows(registry, [
              ["network_boundaries", "Network boundaries"],
              ["user_inputs", "User inputs"],
              ["data_sinks", "Data sinks"],
              ["auth_components", "Auth components"],
            ])}
          />
        </section>

        <section
          className="rounded-2xl border bg-card px-5 py-4 shadow-card"
          style={{ borderColor: "hsl(var(--border-soft))" }}
        >
          <p className="text-sm font-semibold text-txt-primary">Cross-session exposure feed</p>
          <div className="mt-3 space-y-3">
            {serviceExposureFeed?.map((item) => (
              <div
                key={`${item.sessionId}-${item.hotspotClass}-${item.label}`}
                className="rounded-2xl border bg-[#fbf7f1] px-4 py-4"
                style={{ borderColor: "hsl(var(--border-soft))" }}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-txt-primary">{item.repo}</p>
                    <p className="mt-1 text-xs text-txt-tertiary">
                      {item.priority} - {item.hotspotClass}
                    </p>
                  </div>
                  <span className="rounded-full bg-card px-3 py-1 text-[11px] font-medium uppercase tracking-[0.14em] text-txt-secondary">
                    {item.label}
                  </span>
                </div>
              </div>
            ))}
            {serviceExposureFeed?.length === 0 && (
              <p className="text-sm leading-6 text-txt-secondary">
                No cross-session exposure hotspot remains active in the current workspace window.
              </p>
            )}
            {serviceExposureFeed === null && (
              <p className="text-sm leading-6 text-txt-secondary">
                Workspace exposure feed is not available. Current-run exposure hotspots remain visible below.
              </p>
            )}
          </div>
        </section>

        <section
          className="rounded-2xl border bg-card px-5 py-4 shadow-card"
          style={{ borderColor: "hsl(var(--border-soft))" }}
        >
          <p className="text-sm font-semibold text-txt-primary">Exposure hotspots</p>
          <div className="mt-3 space-y-3">
            {hotspots.map((item) => (
              <div
                key={item.id}
                className="rounded-2xl border bg-[#fbf7f1] px-4 py-4"
                style={{ borderColor: "hsl(var(--border-soft))" }}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-txt-primary">{item.label}</p>
                    <p className="mt-1 text-xs text-txt-tertiary">
                      {item.priority} - {item.hotspotClass}
                    </p>
                  </div>
                </div>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <ExposureRow label="Evidence" value={item.evidence} />
                  <ExposureRow label="Next action" value={item.nextAction} />
                </div>
              </div>
            ))}
            {hotspots.length === 0 && (
              <p className="text-sm leading-6 text-txt-secondary">
                No active exposure hotspot remains for the current repository run.
              </p>
            )}
          </div>
        </section>

        <div className="flex items-center justify-end gap-3 border-t pt-4" style={{ borderColor: "hsl(var(--border-primary))" }}>
          <button
            onClick={onBack}
            className="rounded-xl border bg-card px-5 py-2 text-sm font-medium text-txt-primary"
            style={{ borderColor: "hsl(var(--border-primary))" }}
          >
            Back
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function ExposureCard({
  icon: Icon,
  label,
  value,
  note,
}: {
  icon: React.ComponentType<{ size?: string | number; className?: string }>;
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="rounded-2xl border bg-card px-4 py-4 shadow-card" style={{ borderColor: "hsl(var(--border-soft))" }}>
      <div className="flex items-center gap-2 text-txt-secondary">
        <Icon size={15} />
        <p className="text-[11px] uppercase tracking-[0.16em] text-txt-tertiary">{label}</p>
      </div>
      <p className="mt-2 text-sm font-semibold text-txt-primary">{value}</p>
      <p className="mt-2 text-xs leading-5 text-txt-secondary">{note}</p>
    </div>
  );
}

function ExposureTable({
  title,
  rows,
}: {
  title: string;
  rows: Array<{ label: string; value: string }>;
}) {
  return (
    <section className="rounded-2xl border bg-card px-5 py-4 shadow-card" style={{ borderColor: "hsl(var(--border-soft))" }}>
      <p className="text-sm font-semibold text-txt-primary">{title}</p>
      <div className="mt-3 space-y-2">
        {rows.map((row) => (
          <div key={row.label} className="flex items-center justify-between gap-3 rounded-xl bg-[#fbf7f1] px-4 py-3">
            <span className="text-sm text-txt-secondary">{row.label}</span>
            <span className="text-right text-sm font-medium text-txt-primary">{row.value}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function ExposureRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border bg-card px-4 py-4" style={{ borderColor: "hsl(var(--border-soft))" }}>
      <p className="text-[11px] uppercase tracking-[0.16em] text-txt-tertiary">{label}</p>
      <p className="mt-2 text-sm leading-6 text-txt-secondary">{value}</p>
    </div>
  );
}

function buildRows(
  source: Record<string, unknown> | null,
  mappings: Array<[string, string]>,
): Array<{ label: string; value: string }> {
  return mappings.map(([key, label]) => ({
    label,
    value: formatUnknown(source?.[key]),
  }));
}

function formatUnknown(value: unknown): string {
  if (value === null || value === undefined) return "Not captured";
  if (Array.isArray(value)) return value.length > 0 ? value.join(", ") : "Not captured";
  if (typeof value === "object") return Object.keys(value as Record<string, unknown>).length > 0 ? JSON.stringify(value) : "Not captured";
  const text = String(value).trim();
  return text.length > 0 ? text : "Not captured";
}
