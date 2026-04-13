import { Link } from "react-router-dom";
import { Download, ArrowRight, Search, AlertTriangle, FileText, Wrench, GitCompare, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageHero } from "@/components/PageHero";
import { WorkflowStep } from "@/components/WorkflowStep";
import { SectionShell, SectionHeader } from "@/components/SectionShell";
import { SpotlightSection } from "@/components/SpotlightSection";
import { ProductMockup, DiffMockup, AgentMockup } from "@/components/ProductMockup";
import { motion } from "framer-motion";

const steps = [
  { icon: Search, title: "Start a Scan", description: "Point SecureScan Studio at your project or repository. The scanner analyzes your source code for known vulnerability patterns, insecure configurations, and risky code constructs." },
  { icon: AlertTriangle, title: "Review Findings", description: "Scan results are organized in a structured findings panel. Each issue includes its severity, affected file, line number, and a clear description of the vulnerability." },
  { icon: FileText, title: "Understand Risk and Severity", description: "Every finding is classified by severity — critical, high, medium, low. Contextual explanations help you understand why each issue matters and what the potential impact is." },
  { icon: Wrench, title: "Generate Fixes", description: "SecureScan Studio generates actionable fix suggestions for each finding. You see the proposed code change, the rationale behind it, and the security improvement it delivers." },
  { icon: GitCompare, title: "Review Patch Quality", description: "Before accepting any fix, review the generated patch in a clean diff view. Inspect every line change, understand the modification, and decide whether to apply, adjust, or skip." },
  { icon: Clock, title: "Save and Continue Later", description: "Every scan creates a session you can save and revisit. Pick up where you left off, compare findings across sessions, and maintain a complete audit trail of your security work." },
];

export default function Workflow() {
  return (
    <>
      <PageHero
        overline="Workflow"
        title={
          <>
            From scan to <span className="serif-accent">resolution</span>,
            <br />
            step by step
          </>
        }
        subtitle="SecureScan Studio guides you through a clear, repeatable workflow for every security review. Scan your code, review findings, generate fixes, validate patches, and track your progress — all in one focused workspace."
      >
        <Link to="/download">
          <Button size="lg" className="gap-2">
            <Download className="w-4 h-4" />
            Download
          </Button>
        </Link>
        <Link to="/features">
          <Button variant="outline" size="lg" className="gap-2">
            Explore Features
            <ArrowRight className="w-4 h-4" />
          </Button>
        </Link>
      </PageHero>

      {/* Visual Journey */}
      <SectionShell dotted>
        <SectionHeader
          overline="The Journey"
          title="A structured path through every security review"
          subtitle="Each step is designed to reduce friction and increase confidence in your security process."
        />
        <div className="max-w-2xl">
          {steps.map((step, i) => (
            <WorkflowStep
              key={step.title}
              step={i + 1}
              title={step.title}
              description={step.description}
              icon={step.icon}
              isLast={i === steps.length - 1}
            />
          ))}
        </div>
      </SectionShell>

      {/* Stage Spotlights */}
      <SpotlightSection
        overline="Step 1 — Scan"
        title="Comprehensive code analysis in seconds"
        description="Select your project, configure the scope, and run a scan. SecureScan Studio performs deep analysis of your source code, identifying vulnerabilities that matter — not just noise."
        visual={<ProductMockup />}
      />

      <SpotlightSection
        reversed
        overline="Steps 2–3 — Review & Assess"
        title="Understand every finding before you act"
        description="Findings are presented with severity tags, file locations, and contextual explanations. You always know what you're looking at, why it's risky, and what to focus on first."
        visual={
          <div className="rounded-xl border border-border bg-card p-5 shadow-lg space-y-3">
            {[
              { title: "SQL Injection in query builder", sev: "Critical", color: "bg-critical text-critical-bg" },
              { title: "Hardcoded secret in config", sev: "High", color: "bg-high text-high-bg" },
              { title: "Validated input handler", sev: "Resolved", color: "bg-success text-success-bg" },
            ].map((f) => (
              <div key={f.title} className="flex items-center gap-3 p-3 rounded-lg border border-border-soft">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${f.color}`}>{f.sev}</span>
                <span className="text-sm text-foreground">{f.title}</span>
              </div>
            ))}
          </div>
        }
      />

      <SpotlightSection
        overline="Steps 4–5 — Fix & Review"
        title="Generate and validate patches with confidence"
        description="Every fix is generated as a reviewable patch. You see the exact diff, understand the change, and decide whether to apply it — ensuring no surprises reach your codebase."
        visual={<DiffMockup />}
      />

      <SpotlightSection
        reversed
        overline="Step 6 — Track"
        title="Session continuity for ongoing security work"
        description="Scans are saved as sessions you can revisit. Track your progress, compare findings across runs, and maintain a clear record of your security review history."
        visual={
          <div className="rounded-xl border border-border bg-card p-5 shadow-lg">
            <div className="mono-label text-text-tertiary mb-3">Recent Sessions</div>
            {[
              { id: "#14", project: "auth-service", date: "Today", status: "Active" },
              { id: "#13", project: "api-gateway", date: "Apr 8", status: "Complete" },
              { id: "#12", project: "web-client", date: "Apr 5", status: "Complete" },
            ].map((s) => (
              <div key={s.id} className="flex items-center gap-3 p-3 rounded-lg border border-border-soft mb-2">
                <span className="font-mono text-sm font-semibold text-foreground">{s.id}</span>
                <span className="text-sm text-foreground flex-1">{s.project}</span>
                <span className="text-xs text-text-tertiary">{s.date}</span>
                <span className={`text-xs font-medium ${s.status === "Active" ? "text-accent" : "text-success"}`}>{s.status}</span>
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
              Start your first scan today
            </h2>
            <p className="text-dark-muted text-lg mb-8">
              Download SecureScan Studio and experience a structured security workflow from end to end.
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
