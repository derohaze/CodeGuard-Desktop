import { Link } from "react-router-dom";
import { Download, ArrowRight, ShieldCheck, AlertTriangle, CheckCircle, Eye, Clock, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageHero } from "@/components/PageHero";
import { SectionShell, SectionHeader } from "@/components/SectionShell";
import { SpotlightSection } from "@/components/SpotlightSection";
import { SeverityBadge } from "@/components/SeverityBadge";
import { DiffMockup } from "@/components/ProductMockup";
import { motion } from "framer-motion";

export default function SecurityReview() {
  return (
    <>
      <PageHero
        overline="Security Review"
        title={
          <>
            Review security issues
            <br />
            with <span className="serif-accent">clarity</span> and control
          </>
        }
        subtitle="SecureScan Studio gives you a structured environment to review, prioritize, and resolve security findings — with full visibility into severity, context, and patch quality."
      >
        <Link to="/download">
          <Button size="lg" className="gap-2">
            <Download className="w-4 h-4" />
            Download
          </Button>
        </Link>
      </PageHero>

      {/* Severity System */}
      <SectionShell dotted>
        <SectionHeader
          overline="Severity Classification"
          title="Understand risk at a glance"
          subtitle="Every finding is classified by severity so your team knows what to address first. Visual indicators make it easy to scan, filter, and prioritize."
          center
        />
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5 max-w-4xl mx-auto">
          {[
            { sev: "critical" as const, label: "Critical", desc: "Immediate risk. Exploitable vulnerabilities that require urgent attention.", color: "border-critical/30 bg-critical-bg" },
            { sev: "high" as const, label: "High", desc: "Significant risk. Issues that should be resolved in the current review cycle.", color: "border-high/30 bg-high-bg" },
            { sev: "medium" as const, label: "Medium", desc: "Moderate risk. Worth tracking and addressing in upcoming work.", color: "border-border bg-muted" },
            { sev: "resolved" as const, label: "Resolved", desc: "Fixed and validated. The vulnerability has been addressed.", color: "border-success/30 bg-success-bg" },
          ].map((item, i) => (
            <motion.div
              key={item.sev}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className={`p-5 rounded-xl border ${item.color}`}
            >
              <SeverityBadge severity={item.sev} className="mb-3" />
              <h3 className="font-semibold text-foreground mb-1 text-sm">{item.label}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </SectionShell>

      {/* Findings List */}
      <SpotlightSection
        overline="Findings Panel"
        title="A structured view of every security issue"
        description="Findings are organized in a clean, filterable list. Each entry includes the vulnerability title, file location, severity tag, and status — giving reviewers everything they need at a glance."
        visual={
          <div className="rounded-xl border border-border bg-card p-5 shadow-lg space-y-2">
            {[
              { title: "SQL Injection — query builder", sev: "critical" as const, file: "db/queries.ts:42", status: "Open" },
              { title: "Hardcoded API key", sev: "high" as const, file: "config/env.ts:18", status: "Fix Generated" },
              { title: "Weak token generation", sev: "high" as const, file: "auth/token.ts:7", status: "Open" },
              { title: "Input validation added", sev: "resolved" as const, file: "api/handler.ts:31", status: "Resolved" },
              { title: "Missing rate limiting", sev: "critical" as const, file: "api/routes.ts:55", status: "Open" },
            ].map((f) => (
              <div key={f.title} className="flex items-center gap-3 p-3 rounded-lg border border-border-soft hover:border-border transition-colors">
                <SeverityBadge severity={f.sev} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{f.title}</p>
                  <p className="text-xs text-text-tertiary font-mono">{f.file}</p>
                </div>
                <span className={`text-xs font-medium ${f.status === "Resolved" ? "text-success" : f.status === "Fix Generated" ? "text-accent" : "text-text-tertiary"}`}>
                  {f.status}
                </span>
              </div>
            ))}
          </div>
        }
      />

      {/* Patch Review */}
      <SpotlightSection
        reversed
        overline="Patch Review"
        title="Inspect every fix before it ships"
        description="Generated patches are displayed in a clear diff format. Review additions and removals, understand the rationale, and accept or modify the change — all within SecureScan Studio."
        visual={<DiffMockup />}
      />

      {/* Context & Rationale */}
      <SpotlightSection
        overline="Context & Explanation"
        title="Understand the why behind every finding"
        description="Each vulnerability includes a detailed explanation — what the issue is, how it can be exploited, and why the suggested fix addresses it. This turns raw findings into actionable knowledge."
        visual={
          <div className="rounded-xl border border-border bg-card p-5 shadow-lg">
            <div className="mb-4">
              <SeverityBadge severity="critical" className="mb-2" />
              <h4 className="font-semibold text-foreground text-sm">SQL Injection — query builder</h4>
              <p className="text-xs text-text-tertiary font-mono mt-1">db/queries.ts:42</p>
            </div>
            <div className="p-4 rounded-lg bg-surface-code border border-border-soft text-sm text-text-secondary leading-relaxed">
              <p className="mb-2"><strong className="text-foreground">What:</strong> User-supplied input is concatenated directly into a SQL query string without parameterization.</p>
              <p className="mb-2"><strong className="text-foreground">Risk:</strong> An attacker can inject arbitrary SQL commands, potentially accessing or modifying database contents.</p>
              <p><strong className="text-foreground">Fix:</strong> Replace string concatenation with parameterized queries to ensure user input is treated as data, not executable code.</p>
            </div>
          </div>
        }
      />

      {/* Before / After */}
      <SectionShell dotted>
        <SectionHeader
          overline="Before & After"
          title="See the transformation"
          subtitle="Review the exact code changes from vulnerable to secure — with clear, side-by-side comparison."
          center
        />
        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, x: -16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="rounded-xl border border-critical/20 bg-critical-bg overflow-hidden"
          >
            <div className="px-4 py-2 border-b border-critical/10 flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-critical" />
              <span className="text-xs font-medium text-critical">Before — Vulnerable</span>
            </div>
            <div className="p-4 font-mono text-xs leading-6">
              <div className="text-foreground">const query = `SELECT * FROM</div>
              <div className="text-foreground pl-4">users WHERE id = ${`{userId}`}`;</div>
              <div className="text-foreground">db.execute(query);</div>
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: 16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="rounded-xl border border-success/20 bg-success-bg overflow-hidden"
          >
            <div className="px-4 py-2 border-b border-success/10 flex items-center gap-2">
              <CheckCircle className="w-3.5 h-3.5 text-success" />
              <span className="text-xs font-medium text-success">After — Secure</span>
            </div>
            <div className="p-4 font-mono text-xs leading-6">
              <div className="text-foreground">const stmt = db.prepare(</div>
              <div className="text-foreground pl-4">"SELECT * FROM users WHERE id = ?"</div>
              <div className="text-foreground">);</div>
              <div className="text-foreground">const result = stmt.run(userId);</div>
            </div>
          </motion.div>
        </div>
      </SectionShell>

      {/* Audit Trail */}
      <SpotlightSection
        reversed
        overline="Audit Trail"
        title="Track every review decision"
        description="Session history captures your review progress over time. See which findings were addressed, which patches were applied, and maintain a complete trail of your security decisions."
        visual={
          <div className="rounded-xl border border-border bg-card p-5 shadow-lg">
            {[
              { action: "Patch applied", detail: "SQL Injection fix — db/queries.ts", time: "2 min ago", icon: CheckCircle },
              { action: "Finding reviewed", detail: "Hardcoded secret — config/env.ts", time: "5 min ago", icon: Eye },
              { action: "Session started", detail: "Scan #14 — auth-service", time: "12 min ago", icon: Clock },
            ].map((entry) => (
              <div key={entry.detail} className="flex items-start gap-3 p-3 border-b border-border-soft last:border-0">
                <entry.icon className="w-4 h-4 text-text-secondary mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-foreground">{entry.action}</p>
                  <p className="text-xs text-text-tertiary mt-0.5">{entry.detail}</p>
                </div>
                <span className="text-xs text-text-tertiary ml-auto shrink-0">{entry.time}</span>
              </div>
            ))}
          </div>
        }
      />

      {/* CTA */}
      <SectionShell dark dotted className="!py-24">
        <div className="text-center max-w-2xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-dark-text mb-4">
              Review with confidence
            </h2>
            <p className="text-dark-muted text-lg mb-8">
              Download SecureScan Studio and bring structure, clarity, and control to your security reviews.
            </p>
            <Link to="/download">
              <Button size="lg" variant="secondary" className="gap-2">
                <Download className="w-4 h-4" />
                Download
              </Button>
            </Link>
          </motion.div>
        </div>
      </SectionShell>
    </>
  );
}
