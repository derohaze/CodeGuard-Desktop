from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
PROMPT_PACKS = {
    "repository_mapper.md": ("shared_scan_rules.md", "shared_framework_focus.md", "repository_mapper.md"),
    "path_reviewer.md": ("shared_scan_rules.md", "shared_framework_focus.md", "path_reviewer.md"),
    "framework_detector.md": ("shared_framework_focus.md", "framework_detector.md"),
    "explain_prompt.md": ("shared_remediation_rules.md", "explain_prompt.md"),
    "fix_prompt.md": ("shared_remediation_rules.md", "fix_prompt.md"),
    "fix_validator_prompt.md": ("shared_remediation_rules.md", "fix_validator_prompt.md"),
}


def load_prompt(name: str, **replacements: str) -> str:
    template = (PROMPTS_DIR / name).read_text(encoding="utf-8")
    if not replacements:
        return template
    return template.format(**replacements)


def load_prompt_pack(name: str, **replacements: str) -> str:
    parts = PROMPT_PACKS.get(name, (name,))
    return "\n\n".join(load_prompt(part, **replacements).strip() for part in parts if part).strip()
