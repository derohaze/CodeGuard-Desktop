export const vulnerableCode = `def run_script(message: str, script_path: str):
    audit.log("starting script notifier")
    payload = format_payload(message)
    env = build_runtime_env()
    command = f"echo {payload} | {script_path}"

    result = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    stdout, stderr = result.communicate(timeout=30)
    save_audit_record(
        kind="script_runner",
        path=script_path,
        command=command,
        status=result.returncode,
    )

    metrics.increment("notifier.script_runner.calls")
    metrics.observe("notifier.script_runner.duration_ms", 30)

    if result.returncode != 0:
        logger.error("script runner failed", extra={"stderr": stderr.decode("utf-8")})
        raise RuntimeError("notification delivery failed")

    rendered = stdout.decode("utf-8").strip()
    notify_followers(rendered)
    cache_last_delivery(rendered)
    return rendered


def format_payload(message: str) -> str:
    normalized = message.replace("\\n", " ")
    return normalized.strip()`;

export const fixedCode = `def run_script(message: str, script_path: str):
    audit.log("starting script notifier")
    payload = format_payload(message)
    env = build_runtime_env()

    result = subprocess.Popen(
        [script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        shell=False,
        text=False,
    )

    stdout, stderr = result.communicate(
        input=payload.encode("utf-8"),
        timeout=30,
    )
    save_audit_record(
        kind="script_runner",
        path=script_path,
        command=script_path,
        status=result.returncode,
    )

    metrics.increment("notifier.script_runner.calls")
    metrics.observe("notifier.script_runner.duration_ms", 30)

    if result.returncode != 0:
        logger.error("script runner failed", extra={"stderr": stderr.decode("utf-8")})
        raise RuntimeError("notification delivery failed")

    rendered = stdout.decode("utf-8").strip()
    notify_followers(rendered)
    cache_last_delivery(rendered)
    return rendered


def format_payload(message: str) -> str:
    normalized = message.replace("\\n", " ")
    return normalized.strip()`;

export const dataFlow = [
  "Attacker POSTs to /api/incoming/{slug} (unauthenticated)",
  "Payload passes through format_payload() (no escaping for shell)",
  "Rendered message sent to ScriptNotifier.send()",
  "Message interpolated into shell command and executed",
];
