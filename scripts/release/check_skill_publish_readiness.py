from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

if Path(__file__).resolve().suffix == ".py":
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib  # type: ignore


CANONICAL_SKILL_DIR = Path("skills/notestorelab-case-review")
DERIVED_SKILL_PATHS = (
    Path("plugins/notestorelab-codex-plugin/skills/notestorelab-case-review/SKILL.md"),
    Path("starter-bundles/codex/plugins/notestorelab/skills/notestorelab-mcp/SKILL.md"),
    Path("starter-bundles/claude-code/plugins/notestorelab/skills/notestorelab-mcp/SKILL.md"),
    Path("plugins/notestorelab-openclaw-bundle/workspace/skills/notestorelab/SKILL.md"),
    Path("starter-bundles/openclaw/workspace/skills/notestorelab/SKILL.md"),
    Path("public-skills/notestorelab-case-review/SKILL.md"),
)
REPO_URL = "https://github.com/xiaojiou176-open/apple-notes-forensics"
CANONICAL_NAME = "notestorelab-case-review"
PUBLIC_SKILL_DIR = Path("public-skills/notestorelab-case-review")
PUBLIC_SKILL_SEMVER = "1.0.0"


def _load_pyproject(repo_root: Path) -> dict[str, object]:
    with (repo_root / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    _, remainder = text.split("---\n", 1)
    frontmatter_text, _, _ = remainder.partition("\n---\n")
    payload: dict[str, str] = {}
    for line in frontmatter_text.splitlines():
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        payload[key.strip()] = raw_value.strip()
    return payload


def _manifest_scalar(text: str, key: str) -> str | None:
    prefix = f"{key}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _manifest_has_section(text: str, key: str) -> bool:
    prefix = f"{key}:"
    return any(line.startswith(prefix) for line in text.splitlines())


def collect_skill_publish_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []

    canonical_skill = repo_root / CANONICAL_SKILL_DIR / "SKILL.md"
    canonical_manifest = repo_root / CANONICAL_SKILL_DIR / "manifest.yaml"

    if not canonical_skill.exists():
        return [f"missing canonical skill: {canonical_skill.relative_to(repo_root)}"]
    if not canonical_manifest.exists():
        return [f"missing canonical skill manifest: {canonical_manifest.relative_to(repo_root)}"]

    canonical_text = canonical_skill.read_text(encoding="utf-8")
    frontmatter = _frontmatter(canonical_text)
    if frontmatter.get("name") != CANONICAL_NAME:
        errors.append("canonical SKILL.md frontmatter name must stay notestorelab-case-review")
    if not frontmatter.get("description"):
        errors.append("canonical SKILL.md frontmatter is missing description")

    for rel_path in DERIVED_SKILL_PATHS:
        derived_path = repo_root / rel_path
        if not derived_path.exists():
            errors.append(f"missing derived skill copy: {rel_path}")
            continue
        if derived_path.read_text(encoding="utf-8") != canonical_text:
            errors.append(f"derived skill copy drifted from canonical skill: {rel_path}")

    manifest_text = canonical_manifest.read_text(encoding="utf-8")
    for key in (
        "name",
        "description",
        "version",
        "homepage",
        "repository",
        "license",
        "entrypoint",
        "capabilities",
        "scope",
        "runtime",
        "install_guidance",
    ):
        if not _manifest_has_section(manifest_text, key):
            errors.append(f"manifest.yaml is missing required field: {key}")

    if _manifest_scalar(manifest_text, "name") != CANONICAL_NAME:
        errors.append("manifest.yaml name must stay notestorelab-case-review")

    pyproject = _load_pyproject(repo_root)
    project = pyproject.get("project")
    version = project.get("version") if isinstance(project, dict) else None
    if _manifest_scalar(manifest_text, "version") != version:
        errors.append("manifest.yaml version must match pyproject.toml project.version")

    if _manifest_scalar(manifest_text, "homepage") != REPO_URL:
        errors.append("manifest.yaml homepage must point at the canonical GitHub repository")
    if _manifest_scalar(manifest_text, "repository") != REPO_URL:
        errors.append("manifest.yaml repository must point at the canonical GitHub repository")
    if _manifest_scalar(manifest_text, "license") != "MIT":
        errors.append("manifest.yaml license must stay MIT")
    if _manifest_scalar(manifest_text, "entrypoint") != "./SKILL.md":
        errors.append("manifest.yaml entrypoint must stay ./SKILL.md")

    public_skill_dir = repo_root / PUBLIC_SKILL_DIR
    public_skill_manifest = public_skill_dir / "manifest.yaml"
    public_skill_readme = public_skill_dir / "README.md"
    if not public_skill_dir.exists():
        errors.append(f"missing public skill directory: {PUBLIC_SKILL_DIR}")
    if not public_skill_manifest.exists():
        errors.append(f"missing public skill manifest: {public_skill_manifest.relative_to(repo_root)}")
    if not public_skill_readme.exists():
        errors.append(f"missing public skill README: {public_skill_readme.relative_to(repo_root)}")
    if public_skill_manifest.exists():
        public_manifest_text = public_skill_manifest.read_text(encoding="utf-8")
        for token in (
            "schema_version: 1",
            "artifact: public-skill-listing-manifest",
            "name: notestorelab-case-review",
            "version: 1.0.0",
            "display_name: NoteStore Lab Case Review",
            "package_shape: skill-folder",
            "clawhub:",
            "openhands-extensions:",
            "status: ready-but-not-listed",
            "status: folder-ready",
            "submit_via: openclaw skill publish .",
            "submit_via: submit this folder as skills/notestorelab-case-review/ in OpenHands/extensions",
            "canonical_repo_version: 0.1.0.post1",
            "official_listing_state: not-yet-listed",
        ):
            if token not in public_manifest_text:
                errors.append(f"public skill manifest is missing required token: {token}")
    if public_skill_readme.exists():
        public_readme_text = public_skill_readme.read_text(encoding="utf-8")
        for token in (
            "OpenHands/extensions-friendly",
            "ClawHub-style",
            "skills/notestorelab-case-review/SKILL.md",
            "no official OpenHands/extensions listing without fresh PR/read-back",
        ):
            if token not in public_readme_text:
                errors.append(f"public skill README is missing required token: {token}")

    codex_plugin_payload = _load_json(
        repo_root / "plugins/notestorelab-codex-plugin/.codex-plugin/plugin.json"
    )
    if codex_plugin_payload.get("version") != version:
        errors.append("Codex plugin version must match pyproject.toml project.version")
    if codex_plugin_payload.get("homepage") != REPO_URL:
        errors.append("Codex plugin homepage must match the canonical GitHub repository")
    if codex_plugin_payload.get("repository") != REPO_URL:
        errors.append("Codex plugin repository must match the canonical GitHub repository")
    if codex_plugin_payload.get("license") != "MIT":
        errors.append("Codex plugin license must stay MIT")

    marketplace_payload = _load_json(repo_root / ".claude-plugin/marketplace.json")
    plugins = marketplace_payload.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append(".claude-plugin/marketplace.json is missing plugins[]")
    else:
        first_plugin = plugins[0]
        if not isinstance(first_plugin, dict) or first_plugin.get("version") != version:
            errors.append("Claude marketplace plugin version must match pyproject.toml project.version")

    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    distribution_text = (repo_root / "DISTRIBUTION.md").read_text(encoding="utf-8")
    integrations_text = (repo_root / "INTEGRATIONS.md").read_text(encoding="utf-8")
    ecosystem_text = (repo_root / "ECOSYSTEM.md").read_text(encoding="utf-8")
    if "skills/notestorelab-case-review/" not in readme_text:
        errors.append("README.md must mention the canonical independent skill surface")
    if "public-skills/notestorelab-case-review/" not in readme_text:
        errors.append("README.md must mention the OpenHands/ClawHub-facing public skill folder")
    if "independent skill surface" not in distribution_text:
        errors.append("DISTRIBUTION.md must describe the independent skill surface truthfully")
    if "OpenHands/extensions" not in distribution_text:
        errors.append("DISTRIBUTION.md must describe the OpenHands/extensions listing boundary")
    if "canonical independent skill surface" not in integrations_text:
        errors.append("INTEGRATIONS.md must describe the canonical independent skill surface")
    if "OpenHands/extensions-friendly public skill folder" not in integrations_text:
        errors.append("INTEGRATIONS.md must describe the OpenHands-facing public skill folder")
    if "OpenHands/extensions-ready public skill folder" not in ecosystem_text:
        errors.append("ECOSYSTEM.md must describe the OpenHands-facing public skill lane")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    errors = collect_skill_publish_errors(repo_root)
    payload = {"ok": not errors, "errors": errors}
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
