import { motion } from "framer-motion";
import { SeverityBadge } from "./SeverityBadge";

export function ProductMockup({ className }: { className?: string }) {
  return (
    <div className={`rounded-xl border bg-card shadow-xl overflow-hidden ${className || ""}`} style={{ borderColor: "hsl(var(--border-soft))" }}>
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-2.5 bg-surface-sidebar border-b" style={{ borderColor: "hsl(var(--border-soft))" }}>
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-status-critical/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-status-high/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-status-success/60" />
        </div>
        <span className="text-[11px] text-text-tertiary ml-2 font-mono">SecureScan Studio</span>
      </div>

      <div className="flex min-h-[320px] md:min-h-[400px]">
        {/* Sidebar */}
        <div className="w-48 border-r bg-surface-sidebar p-3 hidden sm:block" style={{ borderColor: "hsl(var(--border-soft))" }}>
          <div className="mono-label text-text-tertiary mb-3">Projects</div>
          {["auth-service", "api-gateway", "web-client"].map((p, i) => (
            <div key={p} className={`px-2.5 py-2 rounded-md text-xs mb-1 cursor-pointer transition-colors ${i === 0 ? "bg-muted font-medium text-text-primary" : "text-text-secondary hover:bg-muted/50"}`}>
              {p}
            </div>
          ))}
          <div className="mono-label text-text-tertiary mt-5 mb-3">Sessions</div>
          {["Scan #12 — Today", "Scan #11 — Apr 8"].map((s, i) => (
            <div key={s} className={`px-2.5 py-2 rounded-md text-xs mb-1 ${i === 0 ? "text-text-primary" : "text-text-tertiary"}`}>
              {s}
            </div>
          ))}
        </div>

        {/* Main content */}
        <div className="flex-1 p-4 bg-surface">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-text-primary">Findings</h3>
            <span className="mono-label text-text-tertiary">7 issues</span>
          </div>

          {[
            { title: "SQL Injection in query builder", sev: "critical" as const, file: "db/queries.ts:42" },
            { title: "Hardcoded secret in config", sev: "high" as const, file: "config/env.ts:18" },
            { title: "Insecure random token", sev: "high" as const, file: "auth/token.ts:7" },
            { title: "Missing input validation", sev: "resolved" as const, file: "api/handler.ts:31" },
          ].map((finding, index) => (
            <motion.div
              key={finding.title}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.15, duration: 0.3 }}
              whileHover={{ scale: 1.02, borderColor: "hsl(var(--border))" }}
              whileTap={{ scale: 0.98 }}
              className="flex items-start gap-3 p-3 rounded-lg border mb-2 bg-card cursor-pointer transition-colors"
              style={{ borderColor: "hsl(var(--border-soft))" }}
            >
              <SeverityBadge severity={finding.sev} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">{finding.title}</p>
                <p className="text-xs text-text-tertiary font-mono mt-0.5">{finding.file}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function DiffMockup({ className }: { className?: string }) {
  return (
    <div className={`rounded-xl border border-border bg-card shadow-lg overflow-hidden ${className || ""}`}>
      <div className="flex items-center gap-2 px-4 py-2 bg-surface-sidebar border-b border-border-soft">
        <span className="text-[11px] text-text-tertiary font-mono">Patch Review — db/queries.ts</span>
      </div>
      <div className="p-4 font-mono text-xs leading-6 bg-surface-code">
        <div className="text-destructive/80 bg-critical-bg/50 px-2 py-0.5 rounded">- const query = `SELECT * FROM users WHERE id = ${`{id}`}`;</div>
        <div className="text-success bg-success-bg/50 px-2 py-0.5 rounded mt-1">+ const query = db.prepare("SELECT * FROM users WHERE id = ?");</div>
        <div className="text-success bg-success-bg/50 px-2 py-0.5 rounded">+ const result = query.run(id);</div>
        <div className="text-text-tertiary mt-3 px-2">  // Parameterized query prevents SQL injection</div>
      </div>
    </div>
  );
}

export function DashboardMockup({ className }: { className?: string }) {
  return (
    <div className={`rounded-xl border border-border bg-card shadow-lg overflow-hidden ${className || ""}`}>
      <div className="flex items-center gap-2 px-4 py-2 bg-surface-sidebar border-b border-border-soft">
        <span className="text-[11px] text-text-tertiary font-mono">Security Dashboard</span>
      </div>
      <div className="p-5 bg-surface">
        <div className="grid grid-cols-3 gap-3 mb-4">
          {[
            { label: "Critical", value: "2", color: "text-critical" },
            { label: "High", value: "5", color: "text-high" },
            { label: "Resolved", value: "12", color: "text-success" },
          ].map((stat) => (
            <div key={stat.label} className="p-3 rounded-lg border border-border-soft bg-card text-center">
              <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
              <div className="text-xs text-text-tertiary mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
        <div className="h-20 rounded-lg bg-muted/50 border border-border-soft flex items-end px-3 pb-2 gap-1.5">
          {[40, 65, 30, 80, 55, 70, 45, 60, 35, 75, 50, 20].map((h, i) => (
            <div key={i} className="flex-1 bg-accent/30 rounded-t" style={{ height: `${h}%` }} />
          ))}
        </div>
        <p className="text-[10px] text-text-tertiary mt-2 text-center font-mono">Scan activity — Last 12 sessions</p>
      </div>
    </div>
  );
}

export function AgentMockup({ className }: { className?: string }) {
  return (
    <div className={`rounded-xl border border-border bg-card shadow-lg overflow-hidden ${className || ""}`}>
      <div className="flex items-center gap-2 px-4 py-2 bg-surface-sidebar border-b border-border-soft">
        <span className="text-[11px] text-text-tertiary font-mono">Builder Agent</span>
      </div>
      <div className="p-4 bg-surface space-y-3">
        <div className="p-3 rounded-lg bg-muted/50 border border-border-soft">
          <p className="text-xs text-text-secondary">Analyzing <span className="font-mono text-foreground">auth/token.ts</span> for insecure random generation...</p>
        </div>
        <div className="p-3 rounded-lg bg-accent/5 border border-accent/20">
          <p className="text-xs font-medium text-foreground mb-1">Suggested Remediation</p>
          <p className="text-xs text-text-secondary">Replace <span className="font-mono">Math.random()</span> with a cryptographically secure alternative. This ensures generated tokens cannot be predicted by an attacker.</p>
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 rounded-md bg-primary text-primary-foreground text-xs font-medium">Apply Fix</button>
          <button className="px-3 py-1.5 rounded-md border border-border text-xs text-text-secondary">Review Patch</button>
        </div>
      </div>
    </div>
  );
}
