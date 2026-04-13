from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RealWorldEvalCase:
    name: str
    repo_slug: str
    local_path: Path
    target_type: str
    expected_kind: str
    notes: str


REAL_WORLD_REPO_ROOT = Path(__file__).resolve().parent / "repos"


REAL_WORLD_CASES = [
    RealWorldEvalCase(
        name="owasp_juice_shop",
        repo_slug="juice-shop",
        local_path=REAL_WORLD_REPO_ROOT / "juice-shop",
        target_type="folder",
        expected_kind="vulnerable",
        notes="OWASP Juice Shop benchmark metadata entry. Populate the local path with a clone to enable the scan.",
    ),
    RealWorldEvalCase(
        name="dvwa",
        repo_slug="DVWA",
        local_path=REAL_WORLD_REPO_ROOT / "DVWA",
        target_type="folder",
        expected_kind="vulnerable",
        notes="Damn Vulnerable Web Application benchmark metadata entry.",
    ),
    RealWorldEvalCase(
        name="bwapp",
        repo_slug="bWAPP",
        local_path=REAL_WORLD_REPO_ROOT / "bWAPP",
        target_type="folder",
        expected_kind="vulnerable",
        notes="bWAPP benchmark metadata entry.",
    ),
    RealWorldEvalCase(
        name="webgoat",
        repo_slug="WebGoat",
        local_path=REAL_WORLD_REPO_ROOT / "WebGoat",
        target_type="folder",
        expected_kind="vulnerable",
        notes="OWASP WebGoat benchmark metadata entry.",
    ),
    RealWorldEvalCase(
        name="nodegoat",
        repo_slug="NodeGoat",
        local_path=REAL_WORLD_REPO_ROOT / "NodeGoat",
        target_type="folder",
        expected_kind="vulnerable",
        notes="OWASP NodeGoat benchmark metadata entry.",
    ),
    RealWorldEvalCase(
        name="security_shepherd",
        repo_slug="SecurityShepherd",
        local_path=REAL_WORLD_REPO_ROOT / "SecurityShepherd",
        target_type="folder",
        expected_kind="vulnerable",
        notes="OWASP Security Shepherd benchmark metadata entry.",
    ),
    RealWorldEvalCase(
        name="mutillidae_ii",
        repo_slug="mutillidae",
        local_path=REAL_WORLD_REPO_ROOT / "mutillidae",
        target_type="folder",
        expected_kind="vulnerable",
        notes="Mutillidae II benchmark metadata entry.",
    ),
    RealWorldEvalCase(
        name="altoroj",
        repo_slug="AltoroJ",
        local_path=REAL_WORLD_REPO_ROOT / "AltoroJ",
        target_type="folder",
        expected_kind="vulnerable",
        notes="AltoroJ benchmark metadata entry.",
    ),
    RealWorldEvalCase(
        name="damn_vulnerable_graphql_application",
        repo_slug="Damn-Vulnerable-GraphQL-Application",
        local_path=REAL_WORLD_REPO_ROOT / "Damn-Vulnerable-GraphQL-Application",
        target_type="folder",
        expected_kind="vulnerable",
        notes="Damn Vulnerable GraphQL Application benchmark metadata entry.",
    ),
    RealWorldEvalCase(
        name="microservices_demo",
        repo_slug="microservices-demo",
        local_path=REAL_WORLD_REPO_ROOT / "microservices-demo",
        target_type="folder",
        expected_kind="complex_cleanish",
        notes="Google Cloud microservices-demo benchmark metadata entry for scale, distributed flows, and false positive pressure.",
    ),
    RealWorldEvalCase(
        name="vulhub",
        repo_slug="vulhub",
        local_path=REAL_WORLD_REPO_ROOT / "vulhub",
        target_type="folder",
        expected_kind="vulnerable",
        notes="Vulhub benchmark metadata entry for CVE-rich and multi-stack coverage stress.",
    ),
]
