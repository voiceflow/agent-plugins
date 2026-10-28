"""Refresh the Voiceflow MCP and CLI surface snapshot that the skill reference checks read."""
import argparse
import json
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tests/fixtures/voiceflow-surface.json"
CLI_VERSION = ROOT / "voiceflow/skills/voiceflow-setup/scripts/cli-version.txt"
REPOSITORY = "voiceflow/cli"
SPEC_PATH = ".speakeasy/out.openapi.yaml"
WORKFLOW_PATH = ".speakeasy/workflow.yaml"
# Commands the CLI defines by hand rather than from the spec (internal/cli/*.go at v0.287.0).
HAND_WRITTEN_COMMANDS = ("auth login", "auth logout", "auth whoami", "configure", "docs get",
                         "docs search", "explore", "version", "whoami")
DOCS_MCP_TOOLS = ("ask_voiceflow", "get_voiceflow_changelog", "read_voiceflow_page", "search_voiceflow")
METHODS = {"get", "put", "post", "patch", "delete", "head", "options", "trace"}
WANTED = {"operationId", "x-vf", "x-vf-client-restriction", "x-speakeasy-ignore"}
FILTER = re.compile(r"( *)(?:- +)?filterOperations:\s*")
REF = re.compile(r"v\d+\.\d+\.\d+")
TOOL = re.compile(r"voiceflow_[a-z0-9_]+")
OPERATION = re.compile(r"[a-z][a-z0-9_]*")
COMMAND = re.compile(r"[a-z][a-z0-9-]*(?: [a-z][a-z0-9-]*)*")
KEY = re.compile(r"""(?P<key>"(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s#'"\-?:][^#]*?|-[^\s#]*?)\s*:(?:\s+(?P<rest>.*))?$""")
BLOCK_HEADER = re.compile(r"([|>])([+-]?)([1-9]?)([+-]?)\s*(?:#.*)?")


class SpecError(ValueError):
    pass


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _blank(line):
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def _skip_blank(lines, index):
    while index < len(lines) and _blank(lines[index]):
        index += 1
    return index


def _strip_comment(text):
    match = re.search(r"\s#", text)
    return (text[:match.start()] if match else text).strip()


def _fold(parts):
    """Join the lines of a multi-line flow scalar: a break is a space, an empty line a newline."""
    result = ""
    pending = False
    for part in parts:
        if not part:
            result += "\n"
            pending = False
            continue
        if result and pending:
            result += " "
        result += part
        pending = True
    return result


def _quoted(lines, index, text):
    """Read a quoted scalar that starts at `text` on lines[index] and may continue on later lines."""
    quote, body, parts, position = text[0], [], [], 1
    while True:
        while position < len(text):
            char = text[position]
            if quote == "'" and char == "'":
                if text[position + 1:position + 2] == "'":
                    body.append("'")
                    position += 2
                    continue
                return _fold(parts + ["".join(body)]), index + 1, text[position + 1:]
            if quote == '"' and char == "\\":
                escape = text[position + 1:position + 2]
                if not escape:
                    position += 1
                    break
                if escape == "u":
                    body.append(chr(int(text[position + 2:position + 6], 16)))
                    position += 6
                    continue
                body.append({"n": "\n", "t": "\t", "0": "\0", "/": "/", " ": " "}.get(escape, escape))
                position += 2
                continue
            if quote == '"' and char == '"':
                return _fold(parts + ["".join(body)]), index + 1, text[position + 1:]
            body.append(char)
            position += 1
        parts.append("".join(body).rstrip())
        body = []
        index += 1
        if index >= len(lines):
            raise SpecError("Unterminated quoted scalar")
        text, position = lines[index].strip(), 0


def _scalar(lines, index, rest, indent):
    """Parse the scalar that begins with `rest` on lines[index]; return it and the next line index."""
    if rest[0] in "'\"":
        value, index, tail = _quoted(lines, index, rest)
        if _strip_comment(tail):
            raise SpecError(f"Unexpected text after a quoted scalar: {tail.strip()}")
        return value, index
    if rest.startswith("["):
        if not rest.rstrip().endswith("]"):
            raise SpecError("Multi-line flow sequences are not supported")
        items = [item.strip() for item in rest.strip()[1:-1].split(",") if item.strip()]
        return [_scalar([item], 0, item, 0)[0] for item in items], index + 1
    if rest.startswith("{"):
        if rest.replace(" ", "") != "{}":
            raise SpecError("Flow mappings are not supported")
        return {}, index + 1
    header = BLOCK_HEADER.fullmatch(rest)
    if header:
        return _block_scalar(lines, index, indent, header)
    parts = [_strip_comment(rest)]
    index += 1
    while index < len(lines) and (not lines[index].strip() or _indent(lines[index]) > indent):
        if lines[index].lstrip().startswith("#"):
            break
        parts.append(_strip_comment(lines[index]))
        index += 1
    while parts and not parts[-1]:
        parts.pop()
    return _fold(parts), index


def _block_scalar(lines, index, indent, header):
    style, chomp, explicit = header.group(1), header.group(2) or header.group(4), header.group(3)
    end = index + 1
    while end < len(lines) and (not lines[end].strip() or _indent(lines[end]) > indent):
        end += 1
    body = lines[index + 1:end]
    content = [line for line in body if line.strip()]
    width = indent + int(explicit) if explicit else (min(_indent(line) for line in content) if content else 0)
    text_lines = [line[width:] if line.strip() else "" for line in body]
    trailing = 0
    while text_lines and not text_lines[-1]:
        text_lines.pop()
        trailing += 1
    if style == "|":
        text = "\n".join(text_lines)
    else:
        text, previous = "", None
        for line in text_lines:
            if previous is None:
                text = line
            elif not line or line.startswith(" ") or not previous or previous.startswith(" "):
                text += "\n" + line
            else:
                text += " " + line
            previous = line
    if chomp == "-" or not text_lines:
        return text, end
    return text + "\n" * (1 + trailing if chomp == "+" else 1), end


def _node(lines, index, parent):
    index = _skip_blank(lines, index)
    if index >= len(lines) or _indent(lines[index]) <= parent:
        return None, index
    indent = _indent(lines[index])
    stripped = lines[index].strip()
    if stripped == "-" or stripped.startswith("- "):
        return _sequence(lines, index, indent)
    return _mapping(lines, index, indent)


def _sequence(lines, index, indent):
    items = []
    while True:
        index = _skip_blank(lines, index)
        if index >= len(lines) or _indent(lines[index]) != indent:
            return items, index
        stripped = lines[index].strip()
        if not (stripped == "-" or stripped.startswith("- ")):
            return items, index
        rest = stripped[1:].strip()
        if not rest or (rest[0] not in "'\"[{" and KEY.match(rest)):
            raise SpecError("Only sequences of scalars are supported")
        value, index = _scalar(lines, index, rest, indent)
        items.append(value)


def _mapping(lines, index, indent):
    result = {}
    while True:
        index = _skip_blank(lines, index)
        if index >= len(lines) or _indent(lines[index]) < indent:
            return result, index
        if _indent(lines[index]) > indent:
            raise SpecError(f"Unexpected indentation: {lines[index].strip()}")
        match = KEY.match(lines[index].strip())
        if not match:
            raise SpecError(f"Expected a mapping key: {lines[index].strip()}")
        key = match.group("key")
        if key[0] == "'":
            key = key[1:-1].replace("''", "'")
        elif key[0] == '"':
            key = _quoted([key], 0, key)[0]
        raw = (match.group("rest") or "").strip()
        rest = raw if raw[:1] in ("'", '"') else _strip_comment(raw)
        if key in result:
            raise SpecError(f"Duplicate key: {key}")
        if rest:
            result[key], index = _scalar(lines, index, rest, indent)
            continue
        following = _skip_blank(lines, index + 1)
        if following < len(lines) and _indent(lines[following]) == indent and \
                (lines[following].strip() == "-" or lines[following].strip().startswith("- ")):
            result[key], index = _sequence(lines, following, indent)
        else:
            result[key], index = _node(lines, index + 1, indent)


def parse_block(lines):
    """Parse the YAML subset of the spec's x-vf blocks: block mappings, sequences of scalars,
    and plain, quoted, and block scalars. Anything else raises SpecError."""
    lines = [line.rstrip("\r") for line in lines]
    if any("\t" in line[:_indent(line) + 1] for line in lines if line.strip()):
        raise SpecError("Tab indentation is not supported")
    value, index = _node(lines, 0, -1)
    if _skip_blank(lines, index) < len(lines):
        raise SpecError(f"Unparsed text: {lines[_skip_blank(lines, index)].strip()}")
    return value if value is not None else {}


def _entries(lines, start, end):
    """Split lines[start:end] into top-level entries, returning (key, entry lines) pairs."""
    index = _skip_blank(lines, start)
    if index >= end:
        return []
    indent = _indent(lines[index])
    entries = []
    while index < end:
        line = lines[index]
        if _blank(line):
            index += 1
            continue
        if _indent(line) != indent:
            raise SpecError(f"Unexpected indentation: {line.strip()}")
        match = KEY.match(line.strip())
        if not match:
            raise SpecError(f"Expected a mapping key: {line.strip()}")
        following = index + 1
        while following < end and (_blank(lines[following]) or _indent(lines[following]) > indent
                                   or lines[following].strip().startswith("- ")
                                   and _indent(lines[following]) == indent):
            following += 1
        entries.append((match.group("key").strip("'\""), lines[index:following]))
        index = following
    return entries


def operations(text):
    """Yield the WANTED keys of every operation under `paths`."""
    lines = text.replace("\r\n", "\n").split("\n")
    try:
        start = lines.index("paths:") + 1
    except ValueError:
        raise SpecError("The spec has no top-level paths") from None
    end = next((i for i in range(start, len(lines)) if lines[i][:1] not in ("", " ", "#")), len(lines))
    for _, path_lines in _entries(lines, start, end):
        for method, operation_lines in _entries(path_lines, 1, len(path_lines)):
            if method not in METHODS:
                continue
            selected = []
            for key, entry in _entries(operation_lines, 1, len(operation_lines)):
                if key in WANTED:
                    selected.extend(entry)
            yield parse_block(selected)


def operation_filters(text):
    """Return (operation IDs, exclude) for each filterOperations step in a Speakeasy workflow."""
    lines = text.replace("\r\n", "\n").split("\n")
    filters = []
    for index, line in enumerate(lines):
        match = FILTER.fullmatch(line)
        if not match:
            continue
        end = index + 1
        while end < len(lines) and (_blank(lines[end]) or _indent(lines[end]) > len(match.group(1))):
            end += 1
        options = parse_block(lines[index + 1:end]) or {}
        names = options.get("operations") or []
        if isinstance(names, str):
            names = names.split(",")
        filters.append(({name.strip() for name in names if name.strip()},
                         str(options.get("exclude", "")).lower() == "true"))
    return filters


def in_cli(operation, filters):
    """Whether the CLI build keeps an operation: Speakeasy skips ignored and filtered-out ones."""
    if str(operation.get("x-speakeasy-ignore", "")).lower() == "true":
        return False
    identifier = operation.get("operationId")
    return all((identifier not in names) if exclude else (identifier in names) for names, exclude in filters)


def build_surface(mcp_text, mcp_ref, cli_text, cli_ref, cli_workflow=""):
    tools, refused = {}, {}
    for operation in operations(mcp_text):
        mcp = (operation.get("x-vf") or {}).get("mcp") or {}
        tool, name = mcp.get("tool"), mcp.get("operation")
        if not tool or not name:
            continue
        if not TOOL.fullmatch(tool) or not OPERATION.fullmatch(name):
            raise SpecError(f"Unexpected MCP name: {tool}.{name}")
        tools.setdefault(tool, set()).add(name)
        restriction = operation.get("x-vf-client-restriction") or {}
        if "mcp" in (restriction.get("deniedClientTypes") or []):
            command = ((operation.get("x-vf") or {}).get("cli") or {}).get("command")
            entry = {"when": "conditional" if restriction.get("condition") else "always",
                     "cli": command, "guidance": restriction.get("guidance", "")}
            if restriction.get("condition"):
                entry["condition"] = restriction["condition"]
            refused[f"{tool}.{name}"] = entry
    if not tools:
        raise SpecError("The MCP spec defines no tools")
    commands = dict.fromkeys(HAND_WRITTEN_COMMANDS)
    filters = operation_filters(cli_workflow)
    for operation in operations(cli_text):
        vf = operation.get("x-vf") or {}
        command = (vf.get("cli") or {}).get("command")
        if not command or not in_cli(operation, filters):
            continue
        if not COMMAND.fullmatch(command):
            raise SpecError(f"Unexpected CLI command: {command}")
        if command in commands:
            raise SpecError(f"Duplicate CLI command: {command}")
        mcp = vf.get("mcp") or {}
        commands[command] = f"{mcp['tool']}.{mcp['operation']}" if mcp.get("tool") and mcp.get("operation") else None
    if len(commands) == len(HAND_WRITTEN_COMMANDS):
        raise SpecError("The CLI spec defines no commands")
    return {
        "schema": 1,
        "mcp": {"source": f"{REPOSITORY} {mcp_ref} {SPEC_PATH}",
                "tools": {tool: sorted(names) for tool, names in tools.items()},
                "refused": refused},
        "cli": {"version": cli_ref[1:], "source": f"{REPOSITORY} {cli_ref} {SPEC_PATH}", "commands": commands},
        "docs_mcp": {"tools": sorted(DOCS_MCP_TOOLS)},
    }


def render(surface):
    return json.dumps(surface, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def fetch(url):
    headers = {"User-Agent": "voiceflow-agent-plugins-surface-refresh"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
        return response.read().decode("utf-8")


def latest_ref():
    tag = json.loads(fetch(f"https://api.github.com/repos/{REPOSITORY}/releases/latest")).get("tag_name", "")
    if not REF.fullmatch(tag):
        raise SpecError(f"Unexpected latest release tag: {tag!r}")
    return tag


def spec_text(ref, path, name=SPEC_PATH):
    if path:
        return Path(path).read_text(encoding="utf-8")
    return fetch(f"https://raw.githubusercontent.com/{REPOSITORY}/{ref}/{name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcp-ref", help="voiceflow/cli tag for the MCP surface (default: latest release)")
    parser.add_argument("--cli-ref", help="voiceflow/cli tag for CLI commands (default: the pinned CLI version)")
    parser.add_argument("--mcp-spec", help="Read the MCP spec from this file instead of GitHub")
    parser.add_argument("--cli-spec", help="Read the CLI spec from this file instead of GitHub")
    parser.add_argument("--cli-workflow", help="Read the CLI's Speakeasy workflow from this file instead of GitHub")
    parser.add_argument("--output", default=str(OUTPUT), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.mcp_spec and not args.mcp_ref:
        parser.error("--mcp-spec needs --mcp-ref to name the release it came from")
    cli_ref = args.cli_ref or "v" + CLI_VERSION.read_text(encoding="utf-8").strip()
    mcp_ref = args.mcp_ref or latest_ref()
    for ref in (mcp_ref, cli_ref):
        if not REF.fullmatch(ref):
            parser.error(f"Expected a release tag like v1.2.3, got {ref!r}")
    mcp_text = spec_text(mcp_ref, args.mcp_spec)
    cli_text = mcp_text if cli_ref == mcp_ref and args.cli_spec is None and args.mcp_spec is None \
        else spec_text(cli_ref, args.cli_spec)
    workflow = spec_text(cli_ref, args.cli_workflow, WORKFLOW_PATH)
    surface = build_surface(mcp_text, mcp_ref, cli_text, cli_ref, workflow)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(render(surface).encode("utf-8"))
    tools = surface["mcp"]["tools"]
    print(f"Wrote {output}: {len(tools)} MCP tools, {sum(map(len, tools.values()))} operations, "
          f"{len(surface['mcp']['refused'])} refused ({mcp_ref}); "
          f"{len(surface['cli']['commands'])} CLI commands ({cli_ref}).")


if __name__ == "__main__":
    main()
