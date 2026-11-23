"""Dependency-free structural validation; does not claim model behavior."""
import json
from pathlib import Path
import re
import sys

from skill_references import check_references
from cli_commands import drift_problems as cli_table_problems
from sync_shared_references import drift_problems

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
# The account MCP has two accepted URLs. The hosts in DYNAMIC_URL_HOST_NAMES cap or trim long tool lists, so they add
# `dynamic=true`: the server lists about a dozen tools and runs the rest by name. This needs
# voiceflow/creator-app#24625 deployed. Codex, Claude, ChatGPT, and other hosts use the plain URL. Codex limits
# tool list size only for servers bundled inside a plugin, and OpenAI's plugin guidelines forbid a generic
# executor for operations that are not listed as tools. A package line that names a host and an account MCP
# URL must give that host's URL. The changelog and the eval fixtures keep older URLs on purpose, so only the
# package is checked. The registry entry keeps the full-list URL. The setup guide must name each host below on
# a line that gives its URL, so a host cannot drop out of the table unnoticed.
ACCOUNT_MCP_URL = "https://mcp.voiceflow.com/mcp?version=3"
ACCOUNT_MCP_DYNAMIC_URL = ACCOUNT_MCP_URL + "&dynamic=true"
ACCOUNT_MCP_ENDPOINT = re.compile(r"https://mcp\.voiceflow\.com/mcp(?![\w/-])(?:\?[\w=&%-]+)?")
DYNAMIC_URL_HOST_NAMES = ("Cursor", "Copilot", "Windsurf", "Antigravity")
PLAIN_URL_HOST_NAMES = ("Codex", "Claude", "ChatGPT")
DYNAMIC_URL_HOSTS = re.compile(rf"\b(?:{'|'.join(DYNAMIC_URL_HOST_NAMES)})\b")
PLAIN_URL_HOSTS = re.compile(rf"\b(?:{'|'.join(PLAIN_URL_HOST_NAMES)})\b")
ACCOUNT_URL_GUIDE = "voiceflow/skills/voiceflow-setup/references/mcp.md"
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
# Anthropic's plugin directory takes only these file types from organizations that are not Verified. It judges
# a file by its content, whatever its name, so text must be UTF-8 and must not start with #!, and an image must
# start with its format's signature. A license, a readme, and .gitignore may have no extension.
PACKAGE_TEXT = {".md", ".txt", ".json", ".yaml", ".yml"}
PACKAGE_NAMES = {"LICENSE", "README", ".gitignore"}
PACKAGE_IMAGES = {".png": (b"\x89PNG\r\n\x1a\n",), ".jpg": (b"\xff\xd8\xff",), ".jpeg": (b"\xff\xd8\xff",),
                  ".gif": (b"GIF87a", b"GIF89a"), ".webp": (b"RIFF",), ".ico": (b"\x00\x00\x01\x00",)}
PACKAGE_TYPES = "Markdown, text, JSON, YAML, or a PNG, JPEG, GIF, WebP, or ICO image"
# Customers' assistants run the install blocks in this guide. CI runs the same lines from the scripts in
# scripts/cli/. Each block's first line sets the skill folder; the lines after it must equal the script's
# lines after its own skill folder line. Both read the version and checksums from the skill's files.
INSTALL_GUIDE = "voiceflow/skills/voiceflow-setup/references/installation.md"
CLI_DATA = "voiceflow/skills/voiceflow-setup/scripts"
INSTALL_BLOCKS = {"sh": ("scripts/cli/install-vf.sh", "skill_dir="),
                  "powershell": ("scripts/cli/install-vf.ps1", "$skillDir = ")}
RELEASE_URL = "https://github.com/voiceflow/cli/releases/download/v$version/$asset"
SHA256_HEX = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{64}(?![0-9A-Fa-f])")
OPEN_FENCE = re.compile(r"(`{3,}|~{3,})[ \t]*([\w-]*)")


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


def text_files(root, patterns):
    return sorted({path for pattern in patterns for path in root.glob(pattern) if path.is_file()
                   and "__pycache__" not in path.parts and path.suffix.lower() not in {".pyc", *PACKAGE_IMAGES}})


def account_url_problems(root):
    """Report each account MCP URL in the package that is not one of the two accepted URLs or not the URL of
    the host its line names, and each host that no line of the setup guide names with its URL."""
    problems = []
    for path in text_files(root, ("voiceflow/**/*",)):
        label = path.relative_to(root).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            urls = {match.group() for match in ACCOUNT_MCP_ENDPOINT.finditer(line)}
            for url in sorted(urls - {ACCOUNT_MCP_URL, ACCOUNT_MCP_DYNAMIC_URL}):
                problems.append(f"{label}:{number}: account MCP URL must be {ACCOUNT_MCP_URL} "
                                f"or {ACCOUNT_MCP_DYNAMIC_URL}, not {url}")
            dynamic, plain = DYNAMIC_URL_HOSTS.search(line), PLAIN_URL_HOSTS.search(line)
            if urls and dynamic and plain:
                problems.append(f"{label}:{number}: name {dynamic.group()} and {plain.group()} on separate lines, "
                                "because they use different account MCP URLs")
            elif dynamic and ACCOUNT_MCP_URL in urls:
                problems.append(f"{label}:{number}: {dynamic.group()} uses {ACCOUNT_MCP_DYNAMIC_URL}")
            elif plain and ACCOUNT_MCP_DYNAMIC_URL in urls:
                problems.append(f"{label}:{number}: {plain.group()} uses {ACCOUNT_MCP_URL}")
    guide = root / ACCOUNT_URL_GUIDE
    lines = guide.read_text(encoding="utf-8").splitlines() if guide.is_file() else []
    for hosts, url in ((DYNAMIC_URL_HOST_NAMES, ACCOUNT_MCP_DYNAMIC_URL), (PLAIN_URL_HOST_NAMES, ACCOUNT_MCP_URL)):
        for host in hosts:
            if not any(re.search(rf"\b{host}\b", line) and f"`{url}`" in line for line in lines):
                problems.append(f"{ACCOUNT_URL_GUIDE}: setup must give {host} the account MCP URL {url}")
    return problems


def docs_url_problems(root):
    """Report each docs MCP server URL that is not DOCS_MCP_URL; dated eval reports stay as recorded."""
    problems = []
    for path in text_files(root, DOCS_URL_SCOPE):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in DOCS_MCP_ENDPOINT.finditer(line):
                if match.group() != DOCS_MCP_URL:
                    label = path.relative_to(root).as_posix()
                    problems.append(f"{label}:{number}: docs MCP URL must be {DOCS_MCP_URL}")
    return problems


def package_type_problems(root=ROOT):
    """Report each plugin file in package-files.txt that Anthropic's directory would refuse from an
    organization that is not Verified."""
    problems = []
    for name in (root / "package-files.txt").read_text(encoding="utf-8").splitlines():
        if not name.startswith("voiceflow/"):
            continue
        path, file_name = root / name, name.rsplit("/", 1)[-1]
        suffix = Path(file_name).suffix.lower()
        if not path.is_file():
            problems.append(f"{name}: listed in package-files.txt but missing")
            continue
        data = path.read_bytes()
        if suffix in PACKAGE_IMAGES:
            signature = data.startswith(PACKAGE_IMAGES[suffix]) and (suffix != ".webp" or data[8:12] == b"WEBP")
            if not signature:
                problems.append(f"{name}: content is not a {suffix[1:].upper()} image")
            continue
        if suffix not in PACKAGE_TEXT and file_name not in PACKAGE_NAMES:
            problems.append(f"{name}: the plugin folder takes only {PACKAGE_TYPES}")
            continue
        if data.startswith(b"#!"):
            problems.append(f"{name}: starts with #!")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        if text is None or "\x00" in text:
            problems.append(f"{name}: not UTF-8 text")
        elif suffix == ".json":
            try:
                json.loads(text)
            except ValueError:
                problems.append(f"{name}: not valid JSON")
    return problems


def fenced_blocks(text):
    """Yield (language, lines) for each fenced code block."""
    fence, language, lines = None, None, []
    for line in text.splitlines():
        if fence is None:
            match = OPEN_FENCE.fullmatch(line)
            if match:
                fence, language, lines = match.group(1), match.group(2), []
        elif line.strip() == fence:
            yield language, lines
            fence = None
        else:
            lines.append(line)


def install_step_problems(root=ROOT):
    """Report install steps that type a version or checksum, or that differ from the installers CI runs."""
    problems = []
    text = (root / INSTALL_GUIDE).read_text(encoding="utf-8")
    version = (root / CLI_DATA / "cli-version.txt").read_text(encoding="utf-8").strip()
    if SHA256_HEX.search(text):
        problems.append(f"{INSTALL_GUIDE}: read checksums from {CLI_DATA}/checksums.txt instead of writing one")
    if version in text:
        problems.append(f"{INSTALL_GUIDE}: read the version from {CLI_DATA}/cli-version.txt instead of writing {version}")
    blocks = list(fenced_blocks(text))
    for language, (installer, start) in INSTALL_BLOCKS.items():
        found = [lines for kind, lines in blocks if kind == language]
        if len(found) != 1:
            problems.append(f"{INSTALL_GUIDE}: give exactly one {language} install block, not {len(found)}")
            continue
        steps = found[0]
        if not steps or not steps[0].startswith(start):
            problems.append(f"{INSTALL_GUIDE}: the {language} block must start by setting the skill folder "
                            f"with {start.strip()}")
            continue
        body = "\n".join(steps[1:])
        for needed in ("scripts/cli-version.txt", "scripts/checksums.txt", RELEASE_URL):
            if needed not in body:
                problems.append(f"{INSTALL_GUIDE}: the {language} block must use {needed}")
        script = (root / installer).read_text(encoding="utf-8").splitlines()
        index = next((number for number, line in enumerate(script) if line.startswith(start)), None)
        if index is None or script[index + 1:] != steps[1:]:
            problems.append(f"{INSTALL_GUIDE}: the {language} block differs from {installer} after the line "
                            "that sets the skill folder; change both together")
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
    # This is the source. Its copies in other skills must match it, which drift_problems checks.
    knowledge = (plugin / "skills/voiceflow/references/documentation.md").read_text(encoding="utf-8")
    assert knowledge.startswith("---\n"), "Missing skill package metadata"
    record = dict(line.split(": ", 1) for line in knowledge.split("---", 2)[1].strip().splitlines())
    assert record == {"package": data[0]["name"], "version": data[0]["version"]}, "Skill package version differs"
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
    # Later checks read every package file as text, so report file types first.
    types = package_type_problems(root)
    if types:
        raise ReferenceProblems(types)
    scripts = root / CLI_DATA
    version = (scripts / "cli-version.txt").read_text(encoding="utf-8").strip()
    assert version == "0.335.0", "Update CLI contract fixtures when changing baseline"
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
    # The CLI command table comes from the snapshot first; the sync check then compares its copies with it.
    problems = (cli_table_problems(root) + drift_problems(root) + check_references(root) + docs_url_problems(root)
                + account_url_problems(root) + install_step_problems(root))
    if problems:
        raise ReferenceProblems(problems)
    return len(SKILL_NAMES)


if __name__ == "__main__":
    try:
        count = validate()
    except ReferenceProblems as error:
        print("\n".join(error.problems), file=sys.stderr)
        sys.exit(1)
    print(f"Validated {count} skills, manifests, package file types, checksums, CLI install steps, "
          "the CLI command table, shared reference copies, local references, and MCP and CLI names.")
