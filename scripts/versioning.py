"""Package version files, pull request titles, and version bump rules; stdlib only."""
from collections import Counter
import json
from pathlib import Path
import re
from typing import NamedTuple

# Every file that holds the package version. validate.py checks that they agree,
# the release workflow rewrites them, and pull requests may not edit them.
# MCP Registry server.json versions belong to the servers, so they are not here.
# The write job in .github/workflows/version.yml repeats this list; a test compares them.
VERSION_FILES = (
    "voiceflow/plugin.json",
    "voiceflow/.claude-plugin/plugin.json",
    "voiceflow/.codex-plugin/plugin.json",
    "voiceflow/.cursor-plugin/plugin.json",
    "voiceflow/skills/voiceflow/references/documentation.md",
)
CHANGELOG = "CHANGELOG.md"
UNRELEASED = "Unreleased"
TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert")
LEVELS = ("none", "patch", "minor", "major")
SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
TITLE = re.compile(r"(?P<type>[a-z]+)(?:\((?P<scope>[^()\s]+)\))?(?P<breaking>!)?: (?P<summary>\S.*)")
BREAKING_FOOTER = re.compile(r"^BREAKING[ -]CHANGE: *\S", re.M)
HEADING = re.compile(r"^## (.*)$", re.M)
FRONT_MATTER = re.compile(r"---\n(.*?)\n---\n", re.S)


class Title(NamedTuple):
    type: str
    scope: str | None
    breaking: bool
    summary: str


def parse_title(title):
    """Return the parts of `type(scope)!: summary`, or None when it is not that shape."""
    match = TITLE.fullmatch(title.strip())
    if not match or match["type"] not in TYPES:
        return None
    return Title(match["type"], match["scope"], bool(match["breaking"]), match["summary"])


def is_release_title(title):
    return title is not None and title.type == "chore" and title.scope == "release"


def has_breaking_footer(body):
    return bool(BREAKING_FOOTER.search(body or ""))


def title_level(title, body=""):
    """The bump a merged title and body ask for: none, patch, minor, or major."""
    if (title is not None and title.breaking) or has_breaking_footer(body):
        return "major"
    if title is None:
        return "none"
    return {"feat": "minor", "fix": "patch"}.get(title.type, "none")


def commit_level(message):
    """The bump for one commit message, or None for a release commit, which never counts."""
    subject, _, body = message.strip().partition("\n")
    title = parse_title(subject)
    if is_release_title(title):
        return None
    return title_level(title, body)


def largest(levels):
    return max((level for level in levels if level is not None), key=LEVELS.index, default="none")


def bump(version, level):
    match = SEMVER.fullmatch(version)
    if not match:
        raise ValueError(f"Invalid package version: {version}")
    major, minor, patch = map(int, match.groups())
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if level == "none":
        return version
    raise ValueError(f"Unknown bump level: {level}")


def version_key(version):
    return tuple(map(int, SEMVER.fullmatch(version).groups()))


def version_in(path, text):
    """Read the package version from one VERSION_FILES entry's text."""
    if path.endswith(".json"):
        version = json.loads(text).get("version")
    else:
        front = FRONT_MATTER.match(text)
        found = re.findall(r"^version: (.*)$", front.group(1), re.M) if front else []
        version = found[0] if len(found) == 1 else None
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise ValueError(f"No valid package version in {path}")
    return version


def read_version(root, path):
    return version_in(path, (Path(root) / path).read_text(encoding="utf-8"))


def package_version(root):
    """The one version that every VERSION_FILES entry holds."""
    versions = {path: read_version(root, path) for path in VERSION_FILES}
    if len(set(versions.values())) != 1:
        raise ValueError("Package versions differ: " + ", ".join(f"{p}={v}" for p, v in versions.items()))
    return versions[VERSION_FILES[0]]


def replace_version(path, text, old, new):
    """Change only the version value in one file's text, keeping every other byte."""
    if path.endswith(".json"):
        pattern = re.compile(r'("version"\s*:\s*")' + re.escape(old) + '"')
        updated, count = pattern.subn(lambda match: match.group(1) + new + '"', text)
        expected = json.loads(text) | {"version": new}
        if count != 1 or json.loads(updated) != expected:
            raise ValueError(f"Could not change only the package version in {path}")
    else:
        front = FRONT_MATTER.match(text)
        if not front:
            raise ValueError(f"Missing package metadata in {path}")
        block, count = re.subn(rf"^version: {re.escape(old)}$", f"version: {new}", front.group(1), flags=re.M)
        if count != 1:
            raise ValueError(f"Could not change only the package version in {path}")
        updated = f"---\n{block}\n---\n" + text[front.end():]
    if version_in(path, updated) != new:
        raise ValueError(f"Could not change the package version in {path}")
    return updated


def set_version(root, new):
    """Rewrite every VERSION_FILES entry from the current package version to `new`."""
    root = Path(root)
    old = package_version(root)
    updates = {}
    for path in VERSION_FILES:
        text = (root / path).read_text(encoding="utf-8")
        updates[path] = replace_version(path, text, old, new)
    for path, text in updates.items():
        (root / path).write_bytes(text.encode("utf-8"))
    return old


def unreleased_entries(text):
    """Non-blank lines under `## Unreleased`, or None when that heading is missing."""
    headings = list(HEADING.finditer(text))
    for index, heading in enumerate(headings):
        if heading.group(1) == UNRELEASED:
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            return [line.strip() for line in text[heading.end():end].splitlines() if line.strip()]
    return None


def added_entries(before, after):
    """Lines under `## Unreleased` in `after` that `before` did not have."""
    earlier = Counter(unreleased_entries(before) or [])
    added = []
    for line in unreleased_entries(after) or []:
        if earlier[line]:
            earlier[line] -= 1
        else:
            added.append(line)
    return added


def changelog_problem(text, version):
    """Explain why the changelog headings do not fit `version`, or return None."""
    headings = HEADING.findall(text)
    if headings[:2] != [UNRELEASED, version]:
        return f"CHANGELOG.md must start with ## {UNRELEASED}, then ## {version}"
    return None


def release_changelog(text, version):
    """Move the `## Unreleased` entries under `## version` and start a new empty Unreleased."""
    headings = HEADING.findall(text)
    if headings[:1] != [UNRELEASED]:
        raise ValueError(f"CHANGELOG.md must start with ## {UNRELEASED}")
    if version in headings:
        raise ValueError(f"CHANGELOG.md already has ## {version}")
    if not unreleased_entries(text):
        raise ValueError(f"## {UNRELEASED} in CHANGELOG.md is empty; add the customer-facing changes first")
    return text.replace(f"\n## {UNRELEASED}\n", f"\n## {UNRELEASED}\n\n## {version}\n", 1)
