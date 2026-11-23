"""Merge review fields into the OpenAI package and check it against the documented rules.

Usage:
  python3 -I package_tools.py merge <plugin.json> <review.json>
  python3 -I package_tools.py validate <package-dir> [--surface <voiceflow-surface.json>]

scripts/openai/build_zip.sh runs both steps. The review data lives next to this
file in review.json; reviewer credentials never go into it.

The rules come from developers.openai.com/plugins/deploy/submission.md,
plugins/deploy/submission-errors.md, plugins/build/plugins.md, and the
Agent Plugins 1.0.0 schemas. Errors stop the build. Blockers are printed but
do not stop the build, because the output is a draft that must not be uploaded.
Only standard-library modules are used. Secret matches print a path, never content.
"""

import json
import re
import struct
import sys
from pathlib import Path

PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
PLUGIN_KEYS = {"$schema", "name", "version", "description", "author", "homepage",
               "repository", "license", "keywords", "extensions"}
NAME = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
CATEGORIES = {"Productivity", "Creativity", "Developer Tools", "Business & Operations",
              "Data & Analytics", "Communication", "Education & Research", "Security",
              "Finance", "Healthcare", "Travel", "Entertainment", "Other"}
URL_FIELDS = ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL")
DOCS_TOOLS = re.compile(r"\b(ask_voiceflow|search_voiceflow|read_voiceflow_page|get_voiceflow_changelog)\b")
VF_TOOL = re.compile(r"\bvf_[a-z0-9_]*[a-z0-9]\b")
V3_META_TOOLS = {"vf_describe_operations", "vf_get_started", "vf_skill_list", "vf_skill_load"}
MD_LINK = re.compile(r"\]\(([^)\s]+)\)")
SECRETS = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9]{20,}|\bsk_live_[A-Za-z0-9]{10,}"
                     r"|\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{30,}|\bxox[abprs]-[A-Za-z0-9-]{10,}"
                     r"|\bvfp_[^_\s]{8}_[^_\s]{24}\b|\bVF\.(?:SA|DM)\.[A-Za-z0-9.]{10,}")


class Report:
    def __init__(self):
        self.errors, self.blockers = [], []

    def error(self, message):
        self.errors.append(message)

    def blocker(self, message):
        self.blockers.append(message)


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def merge(plugin_path, review_path):
    plugin, extra = load_json(plugin_path), load_json(review_path)
    openai = plugin.setdefault("extensions", {}).setdefault("com.openai", {})
    for key in ("review", "publication"):
        if key in openai:
            sys.exit(f"{plugin_path} already sets extensions.com.openai.{key}. "
                     "Decide which copy wins before building.")
        openai[key] = extra[key]
    # A resubmission needs a higher version than the rejected upload, even when the plugin files
    # are the same release. review.json's package_version sets the version in the ZIP only.
    if extra.get("package_version"):
        plugin["version"] = extra["package_version"]
    Path(plugin_path).write_text(json.dumps(plugin, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def one_line_text(value, limit, label, report):
    if not isinstance(value, str) or not value.strip():
        report.error(f"{label} is required")
    elif "\n" in value or len(value) > limit:
        report.error(f"{label} must be one line of at most {limit} characters (has {len(value)})")


def image_size(path):
    """Width and height of a PNG, or None for other formats."""
    with open(path, "rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def check_asset(root, field, value, report):
    if not isinstance(value, str) or not value.startswith("./"):
        report.error(f"{field} must be a ./ path inside the plugin")
        return
    path = (root / value).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        report.error(f"{field} points at a missing file or outside the plugin: {value}")
        return
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
        report.error(f"{field} must be PNG, JPEG, WebP, or SVG")
    if path.stat().st_size > 5 * 1024 * 1024:
        report.error(f"{field} is larger than 5 MiB")
    size = image_size(path)
    if size is None:
        report.blocker(f"{field}: size not checked for non-PNG files; check square, 48 to 4096 px")
    elif size[0] != size[1] or not 48 <= size[0] <= 4096:
        report.error(f"{field} must be square and 48 to 4096 px (is {size[0]}x{size[1]})")


def check_manifest(root, report):
    plugin = load_json(root / "plugin.json")
    extra = set(plugin) - PLUGIN_KEYS
    if extra:
        report.error(f"plugin.json has keys outside the Agent Plugins schema: {sorted(extra)}")
    if plugin.get("$schema") != PLUGIN_SCHEMA:
        report.error("plugin.json $schema must be the Agent Plugins 1.0.0 plugin schema")
    if not NAME.match(plugin.get("name", "")) or len(plugin.get("name", "")) > 64:
        report.error("name must be lowercase letters, digits, and single hyphens, at most 64 characters")
    if not SEMVER.match(plugin.get("version", "")):
        report.error("version must be a semantic version such as 1.0.0")
    description = plugin.get("description", "")
    if not description or len(description) > 1024:
        report.error("description is required and must be at most 1024 characters")
    author = plugin.get("author", {})
    if set(author) - {"name", "email", "url"} or not author.get("name") or len(author["name"]) > 120:
        report.error("author must hold name (at most 120 characters), and optionally email and url")

    openai = plugin.get("extensions", {}).get("com.openai")
    if not isinstance(openai, dict):
        report.error("extensions.com.openai is required for this package")
        return plugin, {}
    for key in ("apps", "hooks"):
        if key in openai:
            report.error(f"extensions.com.openai.{key} is set; public submission rejects apps and lifecycle hooks")

    ui = openai.get("interface", {})
    one_line_text(ui.get("displayName"), 30, "interface.displayName", report)
    one_line_text(ui.get("shortDescription"), 30, "interface.shortDescription", report)
    one_line_text(ui.get("developerName"), 80, "interface.developerName", report)
    long_description = ui.get("longDescription", "")
    if not long_description or len(long_description) > 4000:
        report.error("interface.longDescription is required and must be at most 4000 characters")
    if ui.get("category") not in CATEGORIES:
        report.error(f"interface.category must be one of {sorted(CATEGORIES)}")
    capabilities = ui.get("capabilities", [])
    if len(capabilities) > 20 or any(not c or "\n" in c or len(c) > 120 for c in capabilities):
        report.error("interface.capabilities allows 20 one-line entries of at most 120 characters")
    for field in URL_FIELDS:
        value = ui.get(field, "")
        if not value.startswith("https://") or len(value) > 1024 or "@" in value.split("/")[2]:
            report.error(f"interface.{field} must be an HTTPS URL of at most 1024 characters")
    prompts = ui.get("defaultPrompt", [])
    prompts = [prompts] if isinstance(prompts, str) else prompts
    normalized = [" ".join(p.split()).casefold() for p in prompts]
    if len(prompts) > 3 or len(set(normalized)) != len(prompts):
        report.error("interface.defaultPrompt allows at most 3 unique prompts")
    for prompt in prompts:
        if not prompt.strip() or "\n" in prompt or len(prompt) > 128 or "@" in prompt:
            report.error(f"starter prompt must be one line, at most 128 characters, no @mention: {prompt!r}")
    for field in ("logo", "composerIcon"):
        check_asset(root, f"interface.{field}", ui.get(field), report)
    for field in ("logoDark", "composerIconDark"):
        if field in ui:
            check_asset(root, f"interface.{field}", ui[field], report)

    skill = openai.get("onboardingSkill")
    if skill is not None:
        parts = Path(skill).parts
        if not skill.startswith("./") or len(parts) != 3 or parts[0] != "skills" or parts[2] != "SKILL.md" \
                or not (root / skill).is_file():
            report.error(f"onboardingSkill must point at ./skills/<name>/SKILL.md inside the package: {skill}")
    return plugin, openai


def check_mcp(root, report):
    path = root / "mcp.json"
    if not path.is_file():
        report.error("mcp.json is missing; a plugin with an MCP server must include it in the first ZIP")
        return []
    config = load_json(path)
    if config.get("$schema") != MCP_SCHEMA or set(config) - {"$schema", "mcpServers"}:
        report.error("mcp.json must hold only $schema (Agent Plugins 1.0.0) and mcpServers")
    servers = config.get("mcpServers", {})
    if len(servers) != 1:
        report.error(f"plugin-level review cases need exactly one MCP server; mcp.json has {len(servers)}")
    for name, server in servers.items():
        # OpenAI documents extensions.com.openai.auth on a server entry. The public Agent Plugins
        # 1.0.0 schema does not list `extensions` there, so it is the one documented exception.
        if set(server) - {"type", "url", "headers", "extensions"}:
            report.error(f"mcp.json server {name} has unexpected keys: {sorted(set(server) - {'type', 'url', 'headers', 'extensions'})}")
        if server.get("type") != "streamable-http" or not str(server.get("url", "")).startswith("https://"):
            report.error(f"mcp.json server {name} must be streamable-http with an https:// URL")
        if server.get("headers"):
            report.error(f"mcp.json server {name} has headers; public submission rejects nonempty headers")
        auth = server.get("extensions", {}).get("com.openai", {}).get("auth", {})
        if auth.get("type") == "none":
            report.error(f"mcp.json server {name} is OAuth-protected and must not declare auth type none")
        if "clientSecret" in json.dumps(server):
            report.error("mcp.json must not contain clientSecret")
    return [server.get("url", "") for server in servers.values()]


def v3_tool_names(surface_path):
    """The account MCP v3 names for a surface snapshot, as scripts/skill_references.py builds them."""
    surface = load_json(surface_path)["mcp"]
    refused = surface.get("refused", {})
    names = set(V3_META_TOOLS)
    for tool, operations in surface["tools"].items():
        group = tool.removeprefix("voiceflow_")
        for operation in operations:
            if (refused.get(f"{tool}.{operation}") or {}).get("when") != "always":
                names.add(f"vf_{group}_{operation}")
    return names


def check_review(openai, version, surface_path, report):
    text = json.dumps(openai)
    for banned in ("test_credentials", "reviewer_instructions"):
        if banned in text:
            report.error(f"package metadata must not contain {banned}")
    review = openai.get("review", {})
    cases = review.get("test_cases", {})
    positive, negative = cases.get("positive", []), cases.get("negative", [])
    if len(positive) != 5 or len(negative) != 3:
        report.error(f"initial MCP review needs exactly 5 positive and 3 negative cases (has {len(positive)} and {len(negative)})")
    for number, case in enumerate(positive, 1):
        for field in ("description", "prompt", "tools_triggered", "expected_behavior"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                report.error(f"positive case {number} needs {field}")
        if len(case.get("description", "")) > 4000:
            report.error(f"positive case {number} description is longer than 4000 characters")
    for number, case in enumerate(negative, 1):
        for field in ("description", "prompt"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                report.error(f"negative case {number} needs {field}")
    if surface_path:
        served = v3_tool_names(surface_path)
        for number, case in enumerate(positive, 1):
            for name in VF_TOOL.findall(case.get("tools_triggered", "")):
                if name not in served:
                    report.error(f"positive case {number} names {name}, which account MCP v3 does not serve")
    demo = review.get("demo_recording_url", "")
    if not demo.startswith("https://") or demo.endswith(".invalid") or ".invalid/" in demo:
        report.blocker("review.demo_recording_url is a placeholder; record the demo video and set its URL")
    notes = openai.get("publication", {}).get("release_notes", "")
    if not notes.strip():
        report.blocker("publication.release_notes is empty")
    elif version not in notes:
        report.blocker(f"publication.release_notes does not mention version {version}; update review.json")


def front_matter(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        key, _, value = line.partition(":")
        if value and not line.startswith((" ", "\t")):
            fields[key.strip()] = value.strip()
    return None


def check_files(root, report):
    files = [p for p in root.rglob("*")]
    if len(files) > 5000:
        report.error("the archive would have more than 5000 entries")
    seen = {}
    for path in files:
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            report.error(f"symbolic link: {relative}")
        if path.name in {".DS_Store", "Thumbs.db", "desktop.ini"} or "__MACOSX" in path.parts:
            report.error(f"system file: {relative}")
        if len(relative.split("/")) > 20:
            report.error(f"path deeper than 20 segments: {relative}")
        key = relative.casefold()
        if key in seen:
            report.error(f"paths differ only by case: {relative} and {seen[key]}")
        seen[key] = relative
    for name in (".app.json", "hooks", ".mcp.json", ".codex-plugin"):
        if (root / name).exists():
            report.error(f"{name} must not be in this package")
    if any(p.name == "hooks.json" for p in files):
        report.error("lifecycle hooks found; public submission rejects them")

    skills = sorted(p for p in (root / "skills").iterdir() if p.is_dir())
    if not skills:
        report.error("the package needs at least one skill")
    for skill in skills:
        manifest = skill / "SKILL.md"
        fields = front_matter(manifest.read_text(encoding="utf-8")) if manifest.is_file() else None
        if fields is None or not fields.get("name") or not fields.get("description"):
            report.error(f"{skill.name}/SKILL.md needs YAML front matter with name and description")
        elif len(fields["description"]) > 1024:
            report.error(f"{skill.name}/SKILL.md description is longer than 1024 characters")

    for path in files:
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".json", ".py", ".sh", ".ps1"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(root).as_posix()
        if SECRETS.search(text):
            report.error(f"possible credential in {relative}; inspect it without printing the value")
        if path.suffix.lower() != ".md":
            continue
        for target in MD_LINK.findall(text):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                continue
            resolved = (path.parent / target.split("#")[0]).resolve()
            if root.resolve() not in resolved.parents and resolved != root.resolve():
                report.error(f"{relative} links outside the package: {target}")
            elif not resolved.exists():
                report.error(f"{relative} has a broken link: {target}")


def check_docs_fallback(root, mcp_urls, ui, report):
    """Skills that name the public docs tools need the docs server, which this package does not connect."""
    if any("/docs/mcp" in url for url in mcp_urls):
        return
    files = sorted({p.relative_to(root).as_posix() for p in (root / "skills").rglob("*.md")
                    if DOCS_TOOLS.search(p.read_text(encoding="utf-8"))})
    # Since 1.2.0 the shared documentation guide maps each docs tool to the account MCP's
    # vf_docs_* tool, so the skills still answer product questions without the docs server.
    guide = root / "skills" / "voiceflow" / "references" / "documentation.md"
    if guide.is_file() and "vf_docs_ask" in guide.read_text(encoding="utf-8"):
        files = []
    if files:
        report.blocker(f"{len(files)} skill files name docs MCP tools (ask_voiceflow and others) that this "
                       "package does not connect; ship the vf_docs_* fallback first")
    if "docs server" in ui.get("longDescription", ""):
        report.blocker("interface.longDescription says setup adds the docs server, which ChatGPT cannot do; "
                       "fix the text in the repository before the final ZIP")
    # Links between skills are not a blocker here: the ZIP ships every skill, and check_files
    # already fails any link that leaves the package or points at a missing file.


def validate(root, surface_path):
    root = Path(root)
    report = Report()
    plugin, openai = check_manifest(root, report)
    mcp_urls = check_mcp(root, report)
    check_review(openai, plugin.get("version", ""), surface_path, report)
    check_files(root, report)
    check_docs_fallback(root, mcp_urls, openai.get("interface", {}), report)
    for message in report.errors:
        print(f"ERROR    {message}")
    for message in report.blockers:
        print(f"BLOCKER  {message}")
    print(f"{len(report.errors)} errors, {len(report.blockers)} draft blockers")
    return 1 if report.errors else 0


def main(argv):
    if len(argv) >= 3 and argv[0] == "merge":
        merge(argv[1], argv[2])
        return 0
    if len(argv) in (2, 4) and argv[0] == "validate":
        surface = argv[3] if len(argv) == 4 and argv[2] == "--surface" else None
        return validate(argv[1], surface)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
