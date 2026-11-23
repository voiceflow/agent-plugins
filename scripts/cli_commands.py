"""Write the table that pairs each account MCP tool with the Voiceflow CLI command for the same operation.

Some hosts list only part of the account MCP tools. The skills then run a hidden tool's operation with the
`vf` command this table names. The table is a shared reference in the `voiceflow` skill. It comes from
tests/fixtures/voiceflow-surface.json, which scripts/refresh_surface.py writes, so run this script after a
refresh and then scripts/sync_shared_references.py. With --check it writes nothing and exits 1 when the
committed table differs from what a run would write.
"""
import argparse
from pathlib import Path
import sys

from skill_references import load_surface

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("voiceflow/skills/voiceflow/references/cli-commands.md")
COMMAND = "python3 scripts/cli_commands.py"
SYNC = "python3 scripts/sync_shared_references.py"
CLI_FLAGS = "--agent-mode --no-interactive --color never -o json"
PREFIX = "voiceflow_"


def tool_name(slug):
    """Return the v3 tool name of a snapshot operation: `voiceflow_agent.get` is `vf_agent_get`."""
    tool, operation = slug.split(".")
    return f"vf_{tool[len(PREFIX):]}_{operation}"


def cell(text):
    """Keep table cell text on one line and out of the table's own syntax."""
    return " ".join(str(text).split()).replace("|", "\\|")


def single_create(slug):
    """Return the one-item create operation for a batch create, as `create_run` for `create_many_runs`."""
    tool, operation = slug.split(".")
    if not operation.startswith("create_many"):
        return None
    rest = operation[len("create_many"):]
    if rest and not rest.startswith("_"):
        return None
    noun = rest[1:]
    if noun.endswith("s"):
        noun = noun[:-1]
    return f"{tool}.create_{noun}" if noun else f"{tool}.create"


def plan(surface):
    """Sort the snapshot into (table rows, tools with no command, conditional refusals, user-only commands)."""
    by_slug = {}
    for command, slug in surface["cli"]["commands"].items():
        if not slug:
            continue
        if slug in by_slug:
            raise ValueError(f"Two CLI commands run {slug}: vf {by_slug[slug]} and vf {command}")
        by_slug[slug] = command
    refused = surface["mcp"]["refused"]
    rows, missing, conditional, user_only = [], [], [], []
    for tool, operations in surface["mcp"]["tools"].items():
        for operation in operations:
            slug = f"{tool}.{operation}"
            refusal = refused.get(slug) or {}
            if refusal.get("when") == "always":
                # The MCP never serves this tool. The user runs the command; the hand-off guidance covers it.
                command = refusal.get("cli") or by_slug.get(slug)
                if command:
                    user_only.append(command)
                continue
            if refusal:
                conditional.append((tool_name(slug), refusal.get("condition", "")))
            if slug in by_slug:
                rows.append((tool_name(slug), by_slug[slug]))
            else:
                single = single_create(slug)
                missing.append((tool_name(slug), by_slug.get(single) if single else None))
    return sorted(rows), sorted(missing), sorted(conditional), sorted(set(user_only))


def render(surface):
    rows, missing, conditional, user_only = plan(surface)
    version = surface["cli"]["version"]
    mcp_version = surface["mcp"]["source"].split()[1].removeprefix("v")
    source = ("the MCP tools of the same release" if mcp_version == version
              else f"the MCP tools of the CLI {mcp_version} release")
    lines = [
        f"<!-- Generated from the MCP and CLI snapshot by {COMMAND}. Run it instead of editing this file. -->",
        "# Run an account tool with the CLI",
        "",
        "Use this table only for an account MCP tool that your host does not list, as",
        "the [operation contract](operations.md#use-the-cli-for-a-hidden-tool) says.",
        "Each row gives the Voiceflow CLI command that runs the same operation.",
        f"The table matches CLI {version} and {source}.",
        "",
        "MCP fields and CLI flags differ, so read `vf <command> --help` before the",
        f"first call. Add `{CLI_FLAGS}` to each command.",
        "",
        "| MCP tool | CLI command |",
        "| --- | --- |",
    ]
    lines += [f"| `{tool}` | `vf {command}` |" for tool, command in rows]
    if missing:
        lines += [
            "",
            "## Tools with no CLI command",
            "",
            "These tools have no CLI command of their own. A `create_many` tool creates",
            "several items in one call. Where this table names a command, run that",
            "command once for each item instead. Those are separate calls: when one",
            "fails, the items created before it stay.",
            "",
            "| MCP tool | Instead |",
            "| --- | --- |",
        ]
        lines += [f"| `{tool}` | " + (f"`vf {command}`, once per item |" if command else "No CLI command |")
                  for tool, command in missing]
    if conditional:
        lines += [
            "",
            "## Tools the MCP refuses in some cases",
            "",
            "Through the CLI, send only what the MCP would accept. When the MCP would",
            "refuse the request, hand the action to the user.",
            "",
            "| MCP tool | When the MCP refuses it |",
            "| --- | --- |",
        ]
        lines += [f"| `{tool}` | {cell(condition) or 'In some cases'} |" for tool, condition in conditional]
    if user_only:
        lines += [
            "",
            "## Commands only the user runs",
            "",
            "These operations carry a credential or spend money, so they are never MCP",
            "tools. Prepare the command and let the user run it in their own terminal.",
            "Never run one yourself.",
            "",
        ]
        lines += [f"- `vf {command}`" for command in user_only]
    return "\n".join(lines) + "\n"


def drift_problems(root=ROOT):
    """Return one line when the committed table differs from what a run would write."""
    root = root.resolve()
    expected = render(load_surface(root))
    path = root / OUTPUT
    if not path.is_file():
        return [f"{OUTPUT.as_posix()}: missing; run {COMMAND}, then {SYNC}"]
    if path.read_text(encoding="utf-8") != expected:
        return [f"{OUTPUT.as_posix()}: differs from tests/fixtures/voiceflow-surface.json; "
                f"run {COMMAND}, then {SYNC}"]
    return []


def write(root=ROOT):
    """Write the table; return True when the file changed."""
    root = root.resolve()
    path = root / OUTPUT
    data = render(load_surface(root)).encode("utf-8")
    if path.is_file() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return True


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="compare the committed table and write nothing")
    args = parser.parse_args(argv)
    if args.check:
        problems = drift_problems(root)
        print("\n".join(problems) if problems else "The CLI command table matches the snapshot.",
              file=sys.stderr if problems else sys.stdout)
        return 1 if problems else 0
    if write(root):
        print(f"Wrote {OUTPUT.as_posix()}. Run {SYNC} to update the copies.")
    else:
        print(f"{OUTPUT.as_posix()} is already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
