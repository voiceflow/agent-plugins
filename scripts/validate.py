"""Dependency-free structural validation; does not claim model behavior."""
import json
from pathlib import Path
import re
import sys

from skill_references import check_references
from versioning import VERSION_FILES, changelog_problem, read_version

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAMES = {
    "voiceflow", "voiceflow-setup", "voiceflow-build", "voiceflow-prompting",
    "voiceflow-workflows", "voiceflow-functions", "voiceflow-wiring",
    "voiceflow-integrations", "voiceflow-knowledge", "voiceflow-messages",
    "voiceflow-voice", "voiceflow-debug", "voiceflow-transcripts",
    "voiceflow-evaluations", "voiceflow-environments", "voiceflow-widget",
    "voiceflow-phone-numbers",
    "voiceflow-optimize-playbooks",
}
LINK = re.compile(r"\[[^\]]*\]\(([^\s)]+)\)")
# Every docs MCP connection the package creates sends `logging=off`, so the docs
# server keeps only anonymous counts. This requires voiceflow/voiceflow-website#617
# to be deployed. To change the URL, change this value; validate() then lists
# each file that still differs.
DOCS_MCP_URL = "https://www.voiceflow.com/docs/mcp?logging=off"
DOCS_MCP_ENDPOINT = re.compile(r"https://www\.voiceflow\.com/docs/mcp(?![\w/-])(?:\?[\w=&%-]+)?")
DOCS_URL_SCOPE = ("voiceflow/**/*", "*.md", "docs/*.md", "evals/*.md", "scripts/*.py", "tests/*.py")
ACCOUNT_MCP_URL = "https://mcp.voiceflow.com/mcp?version=3"
REGISTRY_SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
SKILLS_SH_SCHEMA = "https://skills.sh/schemas/skills.sh.schema.json"
KEYWORD = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SEMVER = re.compile(r"\d+\.\d+\.\d+")
# Limits from developers.openai.com/plugins/deploy/submission (listing metadata).
INTERFACE_LIMITS = {"displayName": 30, "shortDescription": 30, "longDescription": 4000, "developerName": 80,
                    "category": 80, "websiteURL": 1024, "supportURL": 1024, "privacyPolicyURL": 1024,
                    "termsOfServiceURL": 1024}
# Anthropic's directory reads these from .claude-plugin/plugin.json; each matches an OpenAI interface field.
CLAUDE_LISTING = {"supportUrl": "supportURL", "privacyPolicyUrl": "privacyPolicyURL",
                  "termsOfServiceUrl": "termsOfServiceURL"}


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


def docs_url_problems(root):
    """Report each docs MCP server URL that is not DOCS_MCP_URL; dated eval reports stay as recorded."""
    paths = sorted({path for pattern in DOCS_URL_SCOPE for path in root.glob(pattern) if path.is_file()
                    and "__pycache__" not in path.parts and path.suffix != ".pyc"})
    problems = []
    for path in paths:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in DOCS_MCP_ENDPOINT.finditer(line):
                if match.group() != DOCS_MCP_URL:
                    label = path.relative_to(root).as_posix()
                    problems.append(f"{label}:{number}: docs MCP URL must be {DOCS_MCP_URL}")
    return problems


def prose_words(text):
    """Count words outside fenced code, as Anthropic's directory counts README words."""
    words, is_fenced = 0, False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            is_fenced = not is_fenced
        elif not is_fenced:
            words += len(line.split())
    return words


def validate_listings(root=ROOT):
    """Check the directory listing metadata: manifests, plugin README, skills.sh, and MCP Registry entries."""
    plugin = root / "voiceflow"
    portable = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))
    claude, codex, cursor = (json.loads((plugin / folder / "plugin.json").read_text(encoding="utf-8"))
                             for folder in (".claude-plugin", ".codex-plugin", ".cursor-plugin"))
    for manifest in (portable, claude, codex, cursor):
        for field in ("homepage", "repository", "keywords"):
            assert manifest.get(field) == portable[field], f"Listing field differs between manifests: {field}"
    assert portable["homepage"].startswith("https://") and portable["repository"].startswith("https://github.com/")
    assert portable["keywords"] and all(KEYWORD.fullmatch(word) for word in portable["keywords"]), "Keywords must be lowercase-hyphenated"
    openai = portable["extensions"]["com.openai"]
    interface = openai["interface"]
    for field, limit in INTERFACE_LIMITS.items():
        assert isinstance(interface.get(field), str) and 0 < len(interface[field]) <= limit, f"Invalid interface.{field}"
        if field.endswith("URL"):
            assert interface[field].startswith("https://"), f"interface.{field} must be https"
    capabilities, prompts = interface["capabilities"], interface["defaultPrompt"]
    assert len(capabilities) <= 20 and all(0 < len(item) <= 120 for item in capabilities), "Invalid capabilities"
    assert 0 < len(prompts) <= 3 and len(set(prompts)) == len(prompts), "Use one to three unique default prompts"
    assert all(0 < len(prompt) <= 128 and "@" not in prompt for prompt in prompts), "Invalid default prompt"
    onboarding = openai["onboardingSkill"]
    assert onboarding.startswith("./") and (plugin / onboarding).is_file(), "Onboarding skill missing"
    assert codex["interface"] == interface, "Codex interface differs from plugin.json"
    assert codex["extensions"]["com.openai"]["onboardingSkill"] == onboarding, "Codex onboarding skill differs"
    assert claude["displayName"] == interface["displayName"], "Claude displayName differs"
    assert claude["documentationUrl"].startswith("https://"), "documentationUrl must be https"
    for field, openai_field in CLAUDE_LISTING.items():
        assert claude[field] == interface[openai_field], f"Claude {field} differs from interface.{openai_field}"
    icons = [claude.get("icon"), cursor.get("logo"), interface.get("logo"), interface.get("composerIcon")]
    for icon in filter(None, icons):
        assert (plugin / icon).is_file() and icon.endswith((".png", ".jpg", ".jpeg")), f"Icon file missing: {icon}"
    market = json.loads((root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    assert market["plugins"][0]["category"] == interface["category"], "Marketplace category differs"
    readme = plugin / "README.md"
    assert readme.is_file() and prose_words(readme.read_text(encoding="utf-8")) >= 40, "Plugin README needs 40+ words"
    skills_sh = json.loads((root / "skills.sh.json").read_text(encoding="utf-8"))
    assert skills_sh == {"$schema": SKILLS_SH_SCHEMA, "paths": ["./voiceflow/skills"]}, "skills.sh.json drift"
    # Registry users add the docs server themselves, so its entry omits the package's logging option.
    expected = {ACCOUNT_MCP_URL, DOCS_MCP_URL.split("?")[0]}
    entries = [json.loads(path.read_text(encoding="utf-8"))
               for path in sorted((root / "mcp-registry").glob("*/server.json"))]
    assert {remote["url"] for entry in entries for remote in entry["remotes"]} == expected, "Registry URLs differ"
    assert len({entry["name"] for entry in entries}) == len(entries) == len(expected), "One registry entry per server"
    for entry in entries:
        assert entry["$schema"] == REGISTRY_SCHEMA and SEMVER.fullmatch(entry["version"])
        assert re.fullmatch(r"com\.voiceflow/[a-z0-9-]+", entry["name"]), "Registry names use com.voiceflow/"
        assert 0 < len(entry["description"]) <= 100 and 0 < len(entry["title"]) <= 100
        assert [remote["type"] for remote in entry["remotes"]] == ["streamable-http"]


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
    for path in VERSION_FILES:
        assert read_version(root, path) == data[0]["version"], f"Package version differs: {path}"
    problem = changelog_problem((root / "CHANGELOG.md").read_text(encoding="utf-8"), data[0]["version"])
    assert problem is None, problem
    validate_listings(root)
    portable = json.loads((plugin / "mcp.json").read_text(encoding="utf-8"))
    legacy = json.loads((plugin / ".mcp.json").read_text(encoding="utf-8"))
    assert portable["$schema"] == "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
    for config, transport in ((portable, "streamable-http"), (legacy, "http")):
        assert config["mcpServers"] == {"voiceflow-knowledge": {
            "type": transport, "url": DOCS_MCP_URL}}, "Docs MCP config drift"
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
    problems = check_references(root) + docs_url_problems(root)
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
