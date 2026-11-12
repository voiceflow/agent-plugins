"""Work out the next package version from the commits merged since the last v* tag.

The Version workflow runs this on main with read-only access. It never pushes.
Modes: `none` (nothing to release), `tag` (no v* tag yet: tag the current version
at the commit that set it), and `release` (rewrite the version files and CHANGELOG.md).
"""
import argparse
from pathlib import Path
import subprocess

import versioning

ROOT = Path(__file__).resolve().parents[1]


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                            encoding="utf-8", timeout=60)
    if result.returncode:
        raise RuntimeError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout


def last_tag(root):
    """The highest vX.Y.Z tag reachable from HEAD, without the v, or None."""
    names = git(root, "tag", "--merged", "HEAD", "--list", "v*").split()
    versions = [name[1:] for name in names if versioning.SEMVER.fullmatch(name[1:])]
    return max(versions, key=versioning.version_key, default=None)


def commits_since(root, version):
    """(sha, message) for each first-parent commit after tag v<version>, newest first."""
    output = git(root, "log", "-z", "--first-parent", "--format=%H%n%B", f"v{version}..HEAD")
    commits = []
    for record in output.split("\0"):
        if record.strip():
            sha, _, message = record.strip("\n").partition("\n")
            commits.append((sha, message))
    return commits


def version_at(root, commit):
    try:
        text = git(root, "show", f"{commit}:{versioning.VERSION_FILES[0]}")
        return versioning.version_in(versioning.VERSION_FILES[0], text)
    except (RuntimeError, ValueError):
        return None


def version_commit(root, version):
    """The newest first-parent commit that changed the package version to `version`."""
    for commit in git(root, "rev-list", "--first-parent", "HEAD", "--", versioning.VERSION_FILES[0]).split():
        parents = git(root, "rev-list", "--parents", "-n", "1", commit).split()[1:]
        before = version_at(root, parents[0]) if parents else None
        if version_at(root, commit) == version and before != version:
            return commit
    raise ValueError(f"No commit on the first-parent history sets version {version}")


def plan(root, warn=print):
    """Decide what the write job does. Reads Git and the working tree; changes nothing."""
    current = versioning.package_version(root)
    tag = last_tag(root)
    if tag is None:
        return {"mode": "tag", "version": current, "target": version_commit(root, current)}
    if tag != current:
        raise ValueError(f"The package version {current} does not match the last tag v{tag}")
    levels = []
    for sha, message in commits_since(root, tag):
        level = versioning.commit_level(message)
        if level is not None and versioning.parse_title(message.partition("\n")[0]) is None:
            warn(f"::warning::Commit {sha[:12]} has no conventional title; it counts as {level}")
        levels.append(level)
    level = versioning.largest(levels)
    if level == "none":
        return {"mode": "none", "version": current, "target": ""}
    return {"mode": "release", "version": versioning.bump(current, level), "target": "", "level": level}


def apply(root, result):
    """Rewrite the version files and CHANGELOG.md for a `release` plan."""
    root = Path(root)
    changelog = root / versioning.CHANGELOG
    text = versioning.release_changelog(changelog.read_text(encoding="utf-8"), result["version"])
    versioning.set_version(root, result["version"])
    changelog.write_bytes(text.encode("utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="rewrite the files for a release")
    parser.add_argument("--github-output", type=Path, help="append mode, version, and target here")
    args = parser.parse_args(argv)
    try:
        result = plan(ROOT)
        if args.write and result["mode"] == "release":
            apply(ROOT, result)
    except (ValueError, RuntimeError) as error:
        print(f"::error::{error}")
        return 1
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            for key in ("mode", "version", "target"):
                output.write(f"{key}={result[key]}\n")
    descriptions = {
        "none": "No merged change since the last tag needs a release.",
        "tag": f"No v* tag yet: tag {result['version']} at {result['target']}.",
        "release": f"Release {result['version']} ({result.get('level')} change).",
    }
    print(descriptions[result["mode"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
