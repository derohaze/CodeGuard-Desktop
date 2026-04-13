import { SeverityBadge } from "./SeverityBadge";

export function CapabilitiesGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-5">
      {/* Smart Code Scanning — large card */}
      <div className="md:col-span-2 lg:col-span-2 group rounded-2xl border border-border-soft bg-card p-6 lg:p-8 hover:border-border hover:shadow-md transition-all duration-300">
        <div className="flex flex-col lg:flex-row gap-6 lg:gap-10">
          <div className="flex-1 min-w-0">
            <span className="mono-label text-accent mb-3 block">Scanning</span>
            <h3 className="text-xl lg:text-2xl font-bold text-foreground mb-3">
              Smart Code Scanning
            </h3>
            <p className="text-text-secondary leading-relaxed">
              Scans your codebase to find real security issues. Goes beyond simple pattern matching to understand context and classify vulnerabilities by severity. Helps you focus on what matters most.
            </p>
          </div>
          <div className="flex-shrink-0 lg:w-[340px]">
            <div className="space-y-1.5">
              {[
                { title: "SQL Injection (blind) via user input", file: "api/users.ts:127", sev: "critical" as const },
                { title: "AWS Secret Access Key exposed", file: ".env.production:3", sev: "critical" as const },
                { title: "Insecure JWT signing algorithm", file: "auth/jwt.ts:45", sev: "high" as const },
                { title: "SSRF via external API call", file: "services/proxy.ts:89", sev: "high" as const },
                { title: "Weak MD5 hash for passwords", file: "models/user.ts:34", sev: "medium" as const },
                { title: "Missing CORS configuration", file: "server/middleware.ts:12", sev: "medium" as const },
                { title: "Debug mode enabled in production", file: "config/index.ts:8", sev: "low" as const },
                { title: "Outdated dependency (lodash < 4.17.21)", file: "package.json:15", sev: "low" as const },
              ].map((f) => (
                <div key={f.title} className="flex items-center gap-3 px-3 py-2 rounded-lg border border-border-soft/70 bg-surface/50">
                  <SeverityBadge severity={f.sev} className="text-[10px] px-1.5 py-0.5" />
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-foreground truncate">{f.title}</p>
                    <p className="text-[10px] text-text-tertiary font-mono">{f.file}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Suggested Fixes */}
      <div className="group rounded-2xl border border-border-soft bg-card p-6 lg:p-8 hover:border-border hover:shadow-md transition-all duration-300">
        <span className="mono-label text-accent mb-3 block">Remediation</span>
        <h3 className="text-lg font-bold text-foreground mb-2">Suggested Fixes</h3>
        <p className="text-sm text-text-secondary leading-relaxed mb-5">
          Code-level fix suggestions for every finding, ready to review and apply.
        </p>
        <div className="rounded-lg border border-border-soft bg-surface-code p-3 font-mono text-[11px] leading-5">
          <div className="flex items-center gap-2 px-2 pb-2 border-b border-border-soft/50 mb-2">
            <span className="text-text-tertiary text-[10px]">src/config/aws.ts</span>
            <span className="text-accent text-[10px]">Lines 23-26</span>
          </div>
          <div className="space-y-1">
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">23</span>
              <div className="text-text-tertiary">{"const s3Config = {"}</div>
            </div>
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">24</span>
              <div className="text-destructive/80 bg-critical-bg/50 px-1 rounded">
                {"  accessKeyId: 'AKIA...XYZ',"}
              </div>
            </div>
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">24</span>
              <div className="text-success bg-success-bg/50 px-1 rounded">
                {"  accessKeyId: process.env.AWS_ACCESS_KEY_ID,"}
              </div>
            </div>
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">25</span>
              <div className="text-text-tertiary">{"  region: 'us-east-1',"}</div>
            </div>
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">26</span>
              <div className="text-text-tertiary">{"};"}</div>
            </div>
          </div>
          <div className="px-2 pt-2 mt-2 border-t border-border-soft/50 flex items-center gap-2">
            <span className="text-success text-[10px]">✓ AWS credentials moved to secure environment variables</span>
          </div>
        </div>
      </div>

      {/* Patch Review */}
      <div className="group rounded-2xl border border-border-soft bg-card p-6 lg:p-8 hover:border-border hover:shadow-md transition-all duration-300">
        <span className="mono-label text-accent mb-3 block">Review</span>
        <h3 className="text-lg font-bold text-foreground mb-2">Patch Review</h3>
        <p className="text-sm text-text-secondary leading-relaxed mb-5">
          Inspect every change line by line in a structured diff view before shipping.
        </p>
        <div className="rounded-lg border border-border-soft bg-surface-code p-3 font-mono text-[11px] leading-5">
          <div className="flex items-center gap-2 px-2 pb-2 border-b border-border-soft/50 mb-2">
            <span className="text-text-tertiary text-[10px]">src/middleware/auth.ts</span>
            <span className="text-accent text-[10px]">Lines 45-52</span>
          </div>
          <div className="space-y-1">
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">45</span>
              <div className="text-text-tertiary">{"app.use((req, res, next) => {"}</div>
            </div>
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">46</span>
              <div className="text-destructive/80 bg-critical-bg/50 px-1 rounded">
                {"  const token = req.headers.authorization;"}
              </div>
            </div>
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">46</span>
              <div className="text-success bg-success-bg/50 px-1 rounded">
                {"  const token = req.headers['authorization']?.split(' ')[1];"}
              </div>
            </div>
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">47</span>
              <div className="text-text-tertiary">{"  if (!token) return res.status(401).send();"}</div>
            </div>
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">48</span>
              <div className="text-text-tertiary">{"  // JWT validation logic"}</div>
            </div>
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">49</span>
              <div className="text-text-tertiary">{"  next();"}</div>
            </div>
            <div className="flex">
              <span className="text-text-tertiary w-6 text-right pr-2">50</span>
              <div className="text-text-tertiary">{"});"}</div>
            </div>
          </div>
          <div className="px-2 pt-2 mt-2 border-t border-border-soft/50 flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] bg-success-bg text-success font-semibold">+28</span>
            <span className="px-2 py-0.5 rounded text-[10px] bg-critical-bg text-critical font-semibold">-12</span>
          </div>
        </div>
      </div>

      {/* Evidence Extraction */}
      <div className="group rounded-2xl border border-border-soft bg-card p-6 lg:p-8 hover:border-border hover:shadow-md transition-all duration-300">
        <span className="mono-label text-accent mb-3 block">Analysis</span>
        <h3 className="text-lg font-bold text-foreground mb-2">Evidence Extraction</h3>
        <p className="text-sm text-text-secondary leading-relaxed mb-5">
          Context-aware code snippets with vulnerability explanations and attack paths.
        </p>
        <div className="rounded-xl border border-border-soft bg-surface p-4">
          <div className="rounded-lg bg-surface-code border border-border-soft/50 p-4 font-mono text-[11px] leading-5">
            <div className="flex items-center justify-between px-2 pb-3 border-b border-border-soft/50 mb-3">
              <div className="flex items-center gap-2">
                <span className="text-text-tertiary text-[10px]">src/auth/jwt.ts</span>
                <span className="w-1 h-1 rounded-full bg-text-tertiary/40" />
                <span className="text-accent text-[10px]">Lines 67-73</span>
              </div>
              <SeverityBadge severity="critical" className="text-[9px] px-1.5 py-0.5" />
            </div>
            <div className="space-y-1">
              <div className="flex">
                <span className="text-text-tertiary w-7 text-right pr-3 text-[10px]">67</span>
                <div className="text-text-tertiary">{"export function signToken(payload: any) {"}</div>
              </div>
              <div className="flex">
                <span className="text-text-tertiary w-7 text-right pr-3 text-[10px]">68</span>
                <div className="text-destructive/80 bg-critical-bg/50 px-2 rounded">
                  {"  return jwt.sign(payload, SECRET, {"}
                </div>
              </div>
              <div className="flex">
                <span className="text-text-tertiary w-7 text-right pr-3 text-[10px]">69</span>
                <div className="text-destructive/80 bg-critical-bg/50 px-2 rounded">
                  {"    algorithm: 'none'  // CRITICAL"}
                </div>
              </div>
              <div className="flex">
                <span className="text-text-tertiary w-7 text-right pr-3 text-[10px]">70</span>
                <div className="text-text-tertiary">{"  });"}</div>
              </div>
              <div className="flex">
                <span className="text-text-tertiary w-7 text-right pr-3 text-[10px]">71</span>
                <div className="text-text-tertiary">{"}"}</div>
              </div>
            </div>
          </div>
          <div className="mt-3 px-3 py-2 rounded-lg bg-critical-bg/10 border border-critical/20 flex items-start gap-2">
            <span className="text-critical text-xs">⚠</span>
            <span className="text-[11px] text-foreground">JWT 'none' algorithm allows token forgery attacks</span>
          </div>
        </div>
      </div>

      {/* Session Tracking */}
      <div className="group rounded-2xl border border-border-soft bg-card p-6 lg:p-8 hover:border-border hover:shadow-md transition-all duration-300">
        <span className="mono-label text-accent mb-3 block">Continuity</span>
        <h3 className="text-lg font-bold text-foreground mb-2">Session Tracking</h3>
        <p className="text-sm text-text-secondary leading-relaxed mb-5">
          Every scan is saved. Pick up where you left off, compare across reviews.
        </p>
        <div className="space-y-0.5">
          {[
            { id: "SCAN-2026-0410", repo: "main-app", time: "2h ago", findings: 12, status: "In Progress", active: true },
            { id: "SCAN-2026-0408", repo: "api-service", time: "2d ago", findings: 8, status: "Review Complete", active: false },
            { id: "SCAN-2026-0405", repo: "auth-module", time: "5d ago", findings: 15, status: "Fixed", active: false },
            { id: "SCAN-2026-0402", repo: "payment-gw", time: "1w ago", findings: 5, status: "Fixed", active: false },
          ].map((s, i) => (
            <div
              key={s.id}
              className="w-full text-left px-3 py-2.5 rounded-xl hover:bg-muted transition-colors group relative border border-border-soft/50 bg-surface/50"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium text-foreground leading-snug line-clamp-2 pr-2">
                  {s.id}
                </p>
                {s.active && (
                  <span className="w-2 h-2 rounded-full bg-foreground mt-1.5 flex-shrink-0" />
                )}
              </div>
              <div className="flex items-center gap-1.5 mt-1 text-xs text-text-tertiary">
                <span>{s.repo}</span>
                <span>·</span>
                <span>{s.time}</span>
                <span>·</span>
                <span>{s.findings} findings</span>
                <span>·</span>
                <span className={s.active ? "text-foreground" : "text-text-tertiary"}>{s.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Security Agent — wide card */}
      <div className="md:col-span-2 lg:col-span-3 group rounded-2xl border border-border-soft bg-gradient-to-br from-card to-surface p-6 lg:p-8 hover:border-border hover:shadow-md transition-all duration-300">
        <div className="flex flex-col lg:flex-row gap-6 lg:gap-12 items-center">
          <div className="flex-1 min-w-0">
            <span className="mono-label text-accent mb-3 block">AI Assistant</span>
            <h3 className="text-xl lg:text-2xl font-bold text-foreground mb-3">
              Security Agent
            </h3>
            <p className="text-text-secondary leading-relaxed max-w-lg">
              An AI-powered security assistant that analyzes vulnerabilities, provides remediation guidance, and helps you implement secure fixes — all within your development environment.
            </p>
          </div>
          <div className="flex-shrink-0 w-full lg:w-[340px]">
            <div className="rounded-xl border border-border-soft bg-card p-4 space-y-3">
              <div className="p-2.5 rounded-lg bg-muted/50 border border-border-soft">
                <p className="text-[11px] text-text-secondary">
                  Analyzing <span className="font-mono text-foreground font-medium">src/utils/crypto.ts</span> for weak random generation in token creation…
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-accent/5 border border-accent/20">
                <p className="text-[11px] font-medium text-foreground mb-1">Critical Finding</p>
                <p className="text-[11px] text-text-secondary leading-relaxed">
                  <span className="font-mono">Math.random()</span> is predictable and not cryptographically secure. Attackers can brute-force tokens. Use <span className="font-mono">crypto.getRandomValues()</span> or <span className="font-mono">crypto.randomBytes()</span> instead.
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => console.log("Apply Fix clicked")}
                  className="px-3 py-1 rounded-md bg-primary text-primary-foreground text-[11px] font-medium hover:opacity-90 transition-opacity"
                >
                  Apply Fix
                </button>
                <button
                  onClick={() => console.log("View Details clicked")}
                  className="px-3 py-1 rounded-md border border-border text-[11px] text-text-secondary hover:bg-muted transition-colors"
                >
                  View Details
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
