import { Link } from "react-router-dom";
import { Download, ArrowRight, Monitor, BookOpen, FileText, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageHero } from "@/components/PageHero";
import { SectionShell, SectionHeader } from "@/components/SectionShell";
import { motion } from "framer-motion";

const quickStartSteps = [
  { step: "01", title: "Download the application", desc: "Get SecureScan Studio for your desktop. The installer handles everything." },
  { step: "02", title: "Open your project", desc: "Point the scanner at your codebase — local directory or cloned repository." },
  { step: "03", title: "Run your first scan", desc: "Start a scan and review findings in seconds. Explore fixes, review patches, track your session." },
];

const resources = [
  { icon: BookOpen, title: "Documentation", desc: "Comprehensive guides for every feature and workflow." },
  { icon: FileText, title: "Release Notes", desc: "Stay up to date with the latest improvements and fixes." },
  { icon: HelpCircle, title: "Support", desc: "Get help from the team when you need it." },
];

export default function DownloadPage() {
  return (
    <>
      <PageHero
        overline="Get Started"
        title={
          <>
            Download <span className="serif-accent">SecureScan</span> Studio
          </>
        }
        subtitle="A professional desktop workspace for code security scanning, vulnerability analysis, and guided remediation. Get started in minutes."
      />

      {/* Primary CTA */}
      <SectionShell className="!pt-0">
        <div className="max-w-2xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="p-8 rounded-xl border border-border bg-card shadow-lg text-center"
          >
            <div className="w-16 h-16 rounded-2xl bg-primary flex items-center justify-center mx-auto mb-5">
              <Monitor className="w-8 h-8 text-primary-foreground" />
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-2">SecureScan Studio for Desktop</h2>
            <p className="text-text-secondary mb-6 max-w-md mx-auto">
              A focused, professional environment for scanning, fixing, and reviewing code security — built for your desktop.
            </p>
            <Button size="lg" className="gap-2 mb-3">
              <Download className="w-4 h-4" />
              Download Desktop App
            </Button>
            <p className="text-xs text-text-tertiary">Available for macOS, Windows, and Linux</p>
          </motion.div>
        </div>
      </SectionShell>

      {/* Quick Start */}
      <SectionShell dotted>
        <SectionHeader
          overline="Quick Start"
          title="Up and running in three steps"
          center
        />
        <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
          {quickStartSteps.map((s, i) => (
            <motion.div
              key={s.step}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="text-center"
            >
              <div className="text-3xl font-bold text-text-tertiary mb-3 font-mono">{s.step}</div>
              <h3 className="font-semibold text-foreground mb-2">{s.title}</h3>
              <p className="text-sm text-text-secondary leading-relaxed">{s.desc}</p>
            </motion.div>
          ))}
        </div>
      </SectionShell>

      {/* Resources */}
      <SectionShell>
        <SectionHeader overline="Resources" title="Everything you need to get started" center />
        <div className="grid md:grid-cols-3 gap-5 max-w-3xl mx-auto">
          {resources.map((r, i) => (
            <motion.div
              key={r.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="p-6 rounded-xl border border-border-soft bg-card hover:border-border transition-colors text-center"
            >
              <r.icon className="w-6 h-6 text-text-secondary mx-auto mb-3" />
              <h3 className="font-semibold text-foreground mb-1">{r.title}</h3>
              <p className="text-sm text-text-secondary">{r.desc}</p>
            </motion.div>
          ))}
        </div>
      </SectionShell>

      {/* Mini FAQ */}
      <SectionShell dotted>
        <SectionHeader overline="Common Questions" title="Quick answers" center />
        <div className="max-w-2xl mx-auto space-y-4">
          {[
            { q: "Is SecureScan Studio free?", a: "SecureScan Studio offers a free tier for individual developers. Team plans are available for larger organizations." },
            { q: "What platforms are supported?", a: "SecureScan Studio is available for macOS, Windows, and Linux desktops." },
            { q: "How do I update the application?", a: "The app checks for updates automatically and notifies you when a new version is available." },
          ].map((faq) => (
            <div key={faq.q} className="p-5 rounded-xl border border-border-soft bg-card">
              <h4 className="font-semibold text-foreground text-sm mb-2">{faq.q}</h4>
              <p className="text-sm text-text-secondary leading-relaxed">{faq.a}</p>
            </div>
          ))}
          <div className="text-center pt-4">
            <Link to="/faq-contact">
              <Button variant="outline" className="gap-2">
                View All FAQ
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </SectionShell>

      {/* CTA */}
      <SectionShell dark dotted className="!py-24">
        <div className="text-center max-w-2xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-dark-text mb-4">
              Secure your code today
            </h2>
            <p className="text-dark-muted text-lg mb-8">
              Join developers and security teams who use SecureScan Studio to find, fix, and review vulnerabilities with confidence.
            </p>
            <Button size="lg" variant="secondary" className="gap-2">
              <Download className="w-4 h-4" />
              Download Now
            </Button>
          </motion.div>
        </div>
      </SectionShell>
    </>
  );
}
