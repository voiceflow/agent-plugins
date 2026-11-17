"""Copy the shared reference files into every skill that links them.

The shared references live in the `voiceflow` skill's references folder. A skill installed
alone cannot read files outside its own folder, so each skill that links a shared file gets
its own copy. A skill needs a shared file when its SKILL.md or one of its own references
links it, or when a shared file it needs links it. This is computed from the links each run.

Each copy is the fixed NOTICE line followed by the source, byte for byte. With no arguments
the script writes: it creates and rewrites copies, deletes stale ones, and adds or removes
their lines in package-files.txt. It writes nothing else. With --check it writes nothing and
exits 1 when a copy or an inventory line differs from what a run would write.
"""
import argparse
import bisect
import os
from pathlib import Path
import sys

from skill_references import local_targets

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "voiceflow/skills/voiceflow/references"
INVENTORY = "package-files.txt"
COMMAND = "python3 scripts/sync_shared_references.py"
# The same first line in every copy. It holds no path, so a copy never points outside its skill.
NOTICE = ("<!-- Generated copy. Edit the source in the `voiceflow` skill's references folder, "
          f"then run {COMMAND}. -->\n").encode("utf-8")


class Conflict(ValueError):
    """A file without the notice sits where a copy must go, so the script cannot replace it."""


def first_line(path):
    with path.open("rb") as stream:
        return stream.readline()


def label(root, path):
    return path.relative_to(root).as_posix()


def symlinks(root):
    """Return every symlink in the managed tree, folders included, without following any."""
    skills = root / SOURCE
    skills = skills.parent.parent
    found = [path for path in (root / "voiceflow", skills) if path.is_symlink()]
    if not found and skills.is_dir():
        for current, folders, files in os.walk(skills):  # os.walk never follows folder symlinks
            found += [Path(current) / name for name in folders + files if (Path(current) / name).is_symlink()]
    return sorted(found)


def symlink_problems(root):
    return [f"{label(root, path)}: is a symlink; the skills tree may hold only regular files and folders"
            for path in symlinks(root)]


def plan(root):
    """Return (wanted copies as {path: bytes}, existing copies, conflicts) for a repository root."""
    root = root.resolve()
    source = root / SOURCE
    skills = source.parent.parent
    shared = {path.name: path for path in sorted(source.glob("*.md"))}
    links = {name: {target.name for target in local_targets(path, source.parent)
                    if target.parent == source and target.name in shared}
             for name, path in shared.items()}
    wanted, existing = {}, set()
    for skill in sorted(path.parent for path in skills.glob("*/SKILL.md")):
        if skill == source.parent:
            continue
        references = skill / "references"
        copies = {path for path in references.glob("*.md") if first_line(path) == NOTICE}
        existing |= copies
        needed = set()
        for path in sorted(skill.rglob("*.md")):
            if path in copies or (path.parent == references and path.name in shared):
                continue
            needed |= {target.name for target in local_targets(path, skill)
                       if target.parent == references and target.name in shared}
        pending = list(needed)
        while pending:
            for name in links[pending.pop()] - needed:
                needed.add(name)
                pending.append(name)
        for name in sorted(needed):
            wanted[references / name] = NOTICE + shared[name].read_bytes()
    conflicts = {}
    for path in sorted(wanted):
        if path.is_symlink():
            conflicts[path] = "is a symlink; replace it with a regular file"
        elif path.exists() and path not in existing:
            conflicts[path] = (f"this name is reserved for a copy of {SOURCE}/{path.name}; rename the file, "
                               "or delete it if it is an old copy without the notice")
    return wanted, existing, conflicts


def read_inventory(root):
    path = root / INVENTORY
    return path.read_text(encoding="utf-8").splitlines() if path.is_file() else []


def inventory_changes(root, wanted, existing):
    """Return (lines to add, lines to remove) so the inventory lists exactly the wanted copies."""
    lines = set(read_inventory(root))
    wanted_lines = {label(root, path) for path in wanted}
    managed = wanted_lines | {label(root, path) for path in existing}
    shared = {path.name for path in (root / SOURCE).glob("*.md")}
    for line in lines:
        parts = line.split("/")
        # A listed copy path whose file is already gone still counts as a copy line. A file that
        # exists without the notice is hand-written, so its line is never touched.
        if (len(parts) == 5 and parts[:2] == ["voiceflow", "skills"] and parts[2] != "voiceflow"
                and parts[3] == "references" and parts[4] in shared and not (root / line).exists()):
            managed.add(line)
    return sorted(wanted_lines - lines), sorted((managed - wanted_lines) & lines)


def drift_problems(root=ROOT):
    """Return one line per copy or inventory line that differs from what a sync run would write."""
    root = root.resolve()
    # A symlinked folder could point outside the checkout, so nothing else is planned or read.
    problems = symlink_problems(root)
    if problems:
        return problems
    wanted, existing, conflicts = plan(root)
    problems = [f"{label(root, path)}: {reason}" for path, reason in conflicts.items()]
    for path, data in sorted(wanted.items()):
        if path in conflicts:
            continue
        source = f"{SOURCE}/{path.name}"
        if not path.is_file():
            problems.append(f"{label(root, path)}: missing copy of {source}; run {COMMAND}")
        elif path.read_bytes() != data:
            problems.append(f"{label(root, path)}: differs from its source; edit the source at {source} "
                            f"and run {COMMAND}")
    for path in sorted(existing - set(wanted)):
        problems.append(f"{label(root, path)}: stale copy; this skill no longer links {path.name}; run {COMMAND}")
    added, removed = inventory_changes(root, wanted, existing)
    problems += [f"{INVENTORY}: missing {line}; run {COMMAND}" for line in added]
    problems += [f"{INVENTORY}: lists {line}, which is not a needed copy; run {COMMAND}" for line in removed]
    return problems


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    os.chmod(path, 0o644)


def sync(root=ROOT):
    """Make every copy and its inventory line match the sources; return what changed, one line each."""
    root = root.resolve()
    # Refuse before planning: a symlinked references folder would make sync delete files outside the checkout.
    problems = symlink_problems(root)
    if problems:
        raise Conflict("\n".join(problems))
    wanted, existing, conflicts = plan(root)
    if conflicts:
        raise Conflict("\n".join(f"{label(root, path)}: {reason}" for path, reason in conflicts.items()))
    added, removed = inventory_changes(root, wanted, existing)
    changes = []
    for path, data in sorted(wanted.items()):
        if not path.is_file():
            write(path, data)
            changes.append(f"created {label(root, path)}")
        elif path.read_bytes() != data:
            write(path, data)
            changes.append(f"rewrote {label(root, path)}")
    for path in sorted(existing - set(wanted)):
        path.unlink()
        changes.append(f"deleted {label(root, path)}")
    if added or removed:
        lines = [line for line in read_inventory(root) if line not in removed]
        for line in added:
            bisect.insort(lines, line)
        write(root / INVENTORY, ("\n".join(lines) + "\n").encode("utf-8"))
        changes += [f"{INVENTORY}: added {line}" for line in added]
        changes += [f"{INVENTORY}: removed {line}" for line in removed]
    return changes


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="verify the copies and write nothing")
    args = parser.parse_args(argv)
    if args.check:
        problems = drift_problems(root)
        print("\n".join(problems) if problems else "Shared reference copies match their sources.",
              file=sys.stderr if problems else sys.stdout)
        return 1 if problems else 0
    try:
        changes = sync(root)
    except Conflict as error:
        print(error, file=sys.stderr)
        return 1
    print("\n".join(changes) if changes else "Shared reference copies are already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
