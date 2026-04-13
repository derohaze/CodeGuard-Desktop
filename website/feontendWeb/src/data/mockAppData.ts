export interface Finding {
  id: string;
  title: string;
  file: string;
  line: number;
  severity: "critical" | "high";
  category: string;
}

export const findings: Finding[] = [
  {
    id: "1",
    title: "Command injection via subprocess",
    file: "app/services/notifiers/script_runner.py",
    line: 42,
    severity: "critical",
    category: "Injection",
  },
  {
    id: "2",
    title: "Hardcoded API secret",
    file: "config/production.py",
    line: 18,
    severity: "high",
    category: "Secrets",
  },
  {
    id: "3",
    title: "SQL injection in user query",
    file: "api/users.py",
    line: 127,
    severity: "critical",
    category: "Injection",
  },
  {
    id: "4",
    title: "Weak random generation",
    file: "utils/token.py",
    line: 34,
    severity: "high",
    category: "Crypto",
  },
];

export const vulnerableCode = `class ScriptNotifier:
    def send_notification(self, message: str):
        cmd = f"notify-send '{message}'"
        subprocess.Popen(cmd, shell=True)`;

export const fixedCode = `class ScriptNotifier:
    def send_notification(self, message: str):
        args = ["notify-send", message]
        subprocess.Popen(args, shell=False)`;

export const dataFlow = [
  "Attacker sends malicious payload to /api/incoming/{slug} webhook",
  "Webhook handler receives unauthenticated request with message parameter",
  "ScriptNotifier.send_notification() is called with attacker-controlled message",
  "Command is constructed by interpolating message into shell string",
  "subprocess.Popen() executes command with shell=True, enabling command injection",
];

export interface TaskLine {
  type: "header" | "status" | "text";
  text: string;
}

export const taskLines: TaskLine[] = [
  { type: "header", text: "Analyzing vulnerability context..." },
  { type: "text", text: "Reading file: app/services/notifiers/script_runner.py" },
  { type: "text", text: "Identified command injection via subprocess.Popen with shell=True" },
  { type: "status", text: "Generating secure replacement..." },
  { type: "text", text: "Using subprocess.run with argument list instead of shell string" },
  { type: "status", text: "Validating fix..." },
  { type: "text", text: "Fix preserves original functionality while eliminating injection risk" },
  { type: "header", text: "Patch ready" },
];
