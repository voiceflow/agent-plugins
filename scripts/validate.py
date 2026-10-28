"""Dependency-free structural validation; does not claim model behavior."""
import json
from pathlib import Path
import re
import sys

from skill_references import check_references

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAMES = {
    "voiceflow", "voiceflow-setup", "voiceflow-build", "voiceflow-prompting",
    "voiceflow-workflows", "voiceflow-functions", "voiceflow-wiring",
    "voiceflow-integrations", "voiceflow-knowledge", "voiceflow-messages",
    "voiceflow-voice", "voiceflow-debug", "voiceflow-transcripts",
    "voiceflow-evaluations", "voiceflow-environments", "voiceflow-widget",
}
LINK = re.compile(r"\[[^\]]*\]\(([^\s)]+)\)")


class ReferenceProblems(AssertionError):
    def __init__(self, problems):
        super().__init__("\n".join(problems))
        self.problems = problems


def markdown_links(text):
    is_fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            is_fenced = not is_fenced
        elif not is_fenced:
            yield from LINK.findall(line)


def validate(root=ROOT):
    plugin = root / "voiceflow"
    manifests = [plugin / "plugin.json"] + [
        plugin / folder / "plugin.json" for folder in (".claude-plugin", ".codex-plugin", ".cursor-plugin")]
    data = [json.loads(path.read_text(encoding="utf-8")) for path in manifests]
    assert all(m["name"] == "voiceflow" for m in data), "Plugin names differ"
    assert len({m["version"] for m in data}) == 1, "Plugin versions differ"
    assert (root / "LICENSE").read_bytes() == (plugin / "LICENSE").read_bytes()
    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    assert "Copyright (c) 2026 Voiceflow, Inc." in license_text, "Incorrect copyright holder"
    assert all(m["author"]["name"] == "Voiceflow, Inc." and m["license"] == "MIT" for m in data), "License metadata differs"
    assert re.fullmatch(r"\d+\.\d+\.\d+", data[0]["version"]), "Invalid version"
    knowledge = (plugin / "skills/voiceflow/references/documentation.md").read_text(encoding="utf-8")
    assert knowledge.startswith("---\n"), "Missing skill package metadata"
    record = dict(line.split(": ", 1) for line in knowledge.split("---", 2)[1].strip().splitlines())
    assert record == {"package": data[0]["name"], "version": data[0]["version"]}, "Skill package version differs"
    assert len(data[0]["extensions"]["com.openai"]["interface"]["shortDescription"]) <= 30
    portable = json.loads((plugin / "mcp.json").read_text(encoding="utf-8"))
    legacy = json.loads((plugin / ".mcp.json").read_text(encoding="utf-8"))
    assert portable["$schema"] == "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
    for config, transport in ((portable, "streamable-http"), (legacy, "http")):
        assert config["mcpServers"] == {"voiceflow-knowledge": {
            "type": transport, "url": "https://www.voiceflow.com/docs/mcp"}}, "Docs MCP config drift"
    assert data[2]["mcpServers"] == "./.mcp.json", "Missing Codex MCP adapter"
    for folder in (".claude-plugin", ".cursor-plugin", ".agents/plugins"):
        market = json.loads((root / folder / "marketplace.json").read_text(encoding="utf-8"))
        assert market["name"] == "voiceflow-plugins"
        entry = market["plugins"][0]
        source = entry["source"]
        assert (source["path"] if isinstance(source, dict) else source) == "./voiceflow"
    skills = plugin / "skills"
    assert {p.parent.name for p in skills.glob("*/SKILL.md")} == SKILL_NAMES
    for path in skills.glob("*/SKILL.md"):
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"Missing frontmatter: {path}"
        front = text.split("---", 2)[1]
        assert f"name: {path.parent.name}\n" in front
        assert re.search(r"^description: .{30,}$", front, re.M)
        assert "license: MIT\n" in front, f"Missing skill license metadata: {path}"
        assert path.with_name("LICENSE").read_text(encoding="utf-8") == license_text, f"Skill license differs: {path}"
        assert len(text.splitlines()) < 160, f"Skill too large: {path}"
    for path in plugin.rglob("*"):
        assert not path.is_symlink(), f"Symlink in package: {path}"
    scripts = skills / "voiceflow-setup/scripts"
    version = (scripts / "cli-version.txt").read_text(encoding="utf-8").strip()
    assert version == "0.287.0", "Update CLI contract fixtures when changing baseline"
    checksums = (scripts / "checksums.txt").read_text(encoding="utf-8").splitlines()
    assert len(checksums) == 6
    assert all(re.fullmatch(r"[a-f0-9]{64}  vf_(Darwin|Linux|Windows)_(arm64|x86_64)\.(tar\.gz|zip)", line) for line in checksums)
    for path in [*root.glob("*.md"), *root.glob("docs/*.md"), *root.glob("evals/**/*.md")]:
        for link in markdown_links(path.read_text(encoding="utf-8")):
            if "://" not in link and not link.startswith(("#", "mailto:")):
                assert (path.parent / link.split("#")[0]).is_file(), f"Missing docs link: {link}"
    cases = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))["cases"]
    assert len(cases) >= 20 and len({case["id"] for case in cases}) == len(cases)
    for case in cases:
        assert case["required"] and case["forbidden"] and case["fixture"] and case["prompt"]
        assert case["category"] in ("setup", "product")
    problems = check_references(root)
    if problems:
        raise ReferenceProblems(problems)
    return len(SKILL_NAMES)


if __name__ == "__main__":
    try:
        count = validate()
    except ReferenceProblems as error:
        print("\n".join(error.problems), file=sys.stderr)
        sys.exit(1)
    print(f"Validated {count} skills, manifests, checksums, local references, and MCP and CLI names.")
