"""Check a pull request title against what the pull request changes; read-only.

The title becomes the squash commit subject, and the Version workflow reads it
after merge: breaking is major, feat is minor, fix is patch, other types change nothing.
"""
import argparse
import json
from pathlib import Path
import subprocess
from typing import NamedTuple

import versioning

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "voiceflow/"
MIGRATION = ("migrate", "migration")


class Changes(NamedTuple):
    paths: list
    version_edits: list
    added_entries: list


def problems(title, body, changes):
    """Every rule the title breaks, as plain sentences. An empty list passes."""
    parsed = versioning.parse_title(title)
    if parsed is None:
        return ["Write the title as `type(scope)!: summary`, where the scope and ! are optional. "
                "Types: " + ", ".join(versioning.TYPES) + "."]
    found = []
    level = versioning.title_level(parsed)
    if versioning.is_release_title(parsed):
        found.append("Only the release workflow uses `chore(release)`. Pick another type or scope.")
    if versioning.has_breaking_footer(body) and not parsed.breaking:
        found.append("The description has a `BREAKING CHANGE:` footer. Add ! to the title, "
                     "such as `feat!: summary`, or remove the footer.")
    if any(path.startswith(PACKAGE) for path in changes.paths) and level == "none":
        found.append("This pull request changes files under voiceflow/, which customers install. "
                     "Use feat, fix, or a breaking type with !.")
    if changes.version_edits:
        found.append("Do not change the package version. The release workflow sets it after merge. "
                     "Revert the version in: " + ", ".join(changes.version_edits) + ".")
    if level != "none" and not changes.added_entries:
        found.append(f"A {parsed.type}{'!' if parsed.breaking else ''} change needs a customer-facing "
                     f"line under `## {versioning.UNRELEASED}` in CHANGELOG.md.")
    if parsed.breaking and not any(word in line.lower() for line in changes.added_entries
                                   for word in MIGRATION):
        found.append(f"A breaking change needs a line under `## {versioning.UNRELEASED}` that tells "
                     "customers how to migrate, with the word migrate or migration.")
    return found


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                            encoding="utf-8", timeout=60)
    if result.returncode:
        raise RuntimeError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout


def show(root, revision, path):
    try:
        return git(root, "show", f"{revision}:{path}")
    except RuntimeError:
        return None


def version_or_none(path, text):
    try:
        return versioning.version_in(path, text) if text is not None else None
    except ValueError:
        return None


def changes_between(base, head, root=ROOT):
    """What merging `head` onto `base` changes: paths, version edits, new Unreleased lines."""
    paths = [path for path in git(root, "diff", "--name-only", "-z", base, head).split("\0") if path]
    edits = [path for path in versioning.VERSION_FILES if path in paths and
             version_or_none(path, show(root, base, path)) != version_or_none(path, show(root, head, path))]
    added = versioning.added_entries(show(root, base, versioning.CHANGELOG) or "",
                                     show(root, head, versioning.CHANGELOG) or "")
    return Changes(paths, edits, added)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--event", type=Path, required=True, help="the pull_request event payload")
    parser.add_argument("--base", required=True, help="revision the pull request merges into")
    parser.add_argument("--head", required=True, help="revision with the pull request merged")
    args = parser.parse_args(argv)
    pull_request = json.loads(args.event.read_text(encoding="utf-8"))["pull_request"]
    title, body = pull_request["title"], pull_request.get("body") or ""
    found = problems(title, body, changes_between(args.base, args.head, ROOT))
    for problem in found:
        print(f"::error title=Conventional PR title::{problem}")
    if found:
        return 1
    parsed = versioning.parse_title(title)
    print(f"Title passes. Version change after merge: {versioning.title_level(parsed, body)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
