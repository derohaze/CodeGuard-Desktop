from pathlib import Path
import re

from app.infrastructure.services.repository_analysis import read_text, relative_path


def build_service_graph(source_root: Path, files: list[Path]) -> list[dict]:
    edges: list[dict] = []
    service_files: dict[str, list[str]] = {}
    for path in files:
        rel = relative_path(path, source_root)
        service_name = _infer_service_name(rel)
        if service_name:
            service_files.setdefault(service_name, []).append(rel)

    for path in files:
        if path.suffix.lower() not in {".py", ".js", ".ts", ".tsx", ".php", ".java", ".go", ".jsp", ".jspf"}:
            continue
        file_path = relative_path(path, source_root)
        text = read_text(path)
        lowered = text.lower()
        if not any(marker in file_path or marker in text for marker in ("service", "controller", "repository", "dao", "model", "resolver", "graphql")):
            if not any(token in lowered for token in ("_service_addr", "_service_url", "grpc.newclient", "grpc.dial", "handlefunc(", "http://", "https://", "dns:///")):
                continue

        for target in files:
            if target == path:
                continue
            if not _same_language_family(path, target):
                continue
            target_rel = relative_path(target, source_root)
            target_name = target.stem.lower()
            if target_name and target_name in lowered:
                edges.append({"from": file_path, "to": target_rel, "kind": "service_reference"})

        for env_match in re.finditer(r'([A-Z][A-Z0-9_]+_SERVICE_(?:ADDR|URL|HOST))', text):
            normalized = _normalize_service_token(env_match.group(1))
            for target_rel in service_files.get(normalized, []):
                if target_rel != file_path:
                    edges.append({"from": file_path, "to": target_rel, "kind": "service_endpoint"})

        for host_match in re.finditer(r"(?:dns:///|https?://)([a-z0-9-]+service)", lowered):
            normalized = host_match.group(1).replace("-", "")
            for target_rel in service_files.get(normalized, []):
                if target_rel != file_path:
                    edges.append({"from": file_path, "to": target_rel, "kind": "service_host"})

        if path.suffix.lower() in {".go", ".py", ".js", ".ts", ".tsx", ".java"}:
            current_service = _infer_service_name(file_path)
            for target_service, target_files in service_files.items():
                if target_service == current_service:
                    continue
                if target_service and target_service in lowered:
                    edges.append({"from": file_path, "to": target_files[0], "kind": "service_call"})
    return edges[:4000]


def _same_language_family(source: Path, target: Path) -> bool:
    source_suffix = source.suffix.lower()
    target_suffix = target.suffix.lower()
    if source_suffix == ".java":
        return target_suffix in {".java", ".jsp", ".jspf", ".xml"}
    if source_suffix == ".php":
        return target_suffix in {".php", ".jsp", ".jspf"}
    if source_suffix in {".js", ".ts", ".tsx"}:
        return target_suffix in {".js", ".ts", ".tsx"}
    if source_suffix == ".py":
        return target_suffix == ".py"
    if source_suffix == ".go":
        return target_suffix == ".go"
    return False


def _normalize_service_token(token: str) -> str:
    normalized = token.lower().replace("_service_addr", "").replace("_service", "")
    normalized = normalized.replace("_", "")
    return f"{normalized}service" if not normalized.endswith("service") else normalized


def _infer_service_name(relative_file: str) -> str:
    parts = relative_file.split("/")
    if len(parts) >= 2 and parts[0] == "src":
        base = parts[1].lower().replace("-", "")
        return base
    for part in parts:
        normalized = part.lower().replace("-", "")
        if normalized.endswith("service"):
            return normalized
    return ""
