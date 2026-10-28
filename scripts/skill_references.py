"""Check that packaged Markdown names only real MCP operations, CLI commands, skills, and files.

The surface snapshot comes from scripts/refresh_surface.py. Every problem is reported as
`path:line: reason`, so one run lists everything to fix.
"""
import json
from pathlib import Path
from urllib.parse import unquote
import re
import unicodedata

SURFACE = Path("tests/fixtures/voiceflow-surface.json")
INTERNAL_NAMES = re.compile(
    r"\b(?:vf_[a-z]+_\w*|describe_operations|audit_wiring|propose_test|skill_read"
    r"|request_(?:secret|integration|mcp_server|phone_number)|grep_transcripts"
    r"|get_debug_transcript|get_transcript_from_url|diff_environments|check_function"
    r"|wait_for_test_runs|ask_question|set_plan|clear_plan|show_[a-z_]+|Atlas|GLM)\b"
    r"|\b(?i:safe mode|autonomous mode)\b")
LINK = re.compile(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)")
HEADING = re.compile(r" {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*")
HTML_ANCHOR = re.compile(r"<a\s+(?:[^>]*?\s)?(?:id|name)=\"([^\"]+)\"", re.I)
FENCE = re.compile(r"\s*(`{3,}|~{3,})")
TOOL_SPAN = re.compile(r"(voiceflow_[a-z0-9_]+)(?:\.([a-z][a-z0-9_]*))?(?![\w.])")
OPERATION_SPAN = re.compile(r"[a-z][a-z0-9_]*")
OPERATION_GAP = re.compile(r"\s*(?:/\s*|,?\s*operation\s+)?")
SKILL_SPAN = re.compile(r"voiceflow-[a-z0-9][a-z0-9-]*")
MD_PATH_SPAN = re.compile(r"(?:\.{1,2}/)*[\w.-]+(?:/[\w.-]+)+\.md")
TOKEN = re.compile(r"\"(?:[^\"\\]|\\.)*\"|'[^']*'|\S+")
COMMAND_WORD = re.compile(r"[a-z][a-z0-9-]*")
FLAG = re.compile(r"--[a-z0-9][a-z0-9-]*|-[A-Za-z]")
SHELL_SEPARATOR = re.compile(r"&&|\|\||\$\(|[;|()]")
CLI_PREFIX = re.compile(r"\bCLI\s+$")
SKILL_BEFORE = re.compile(r"\bskills?\s+$", re.I)
SKILL_AFTER = re.compile(r"\s*skills?\b", re.I)
BACKTICKS = re.compile(r"`+")


def load_surface(root):
    return json.loads((root / SURFACE).read_text(encoding="utf-8"))


def parse(text):
    """Split Markdown into prose blocks, fenced command lines, and headings, keeping line numbers."""
    prose, fenced, headings, block = [], [], [], []
    fence, pending = None, None

    def flush():
        if block:
            prose.append((block[0][0], "\n".join(content for _, content in block)))
            block.clear()

    for number, line in enumerate(text.splitlines(), 1):
        opener = FENCE.match(line)
        if opener and opener.group(1)[0] == "`" and "`" in line[opener.end():]:
            opener = None
        if fence:
            if opener and opener.group(1)[0] == fence[0] and len(opener.group(1)) >= len(fence) \
                    and not line[opener.end():].strip():
                fence = None
                if pending:
                    fenced.append(pending)
                    pending = None
                continue
            stripped = line.rstrip()
            if pending:
                pending = (pending[0], pending[1] + " " + stripped.strip())
            else:
                pending = (number, stripped)
            if stripped.endswith(("\\", " `")):
                pending = (pending[0], pending[1].rstrip("\\`").rstrip())
            else:
                fenced.append(pending)
                pending = None
            continue
        if opener:
            flush()
            fence = opener.group(1)
            continue
        if line.strip():
            block.append((number, line))
            heading = HEADING.fullmatch(line)
            if heading:
                headings.append(heading.group(2) or "")
        else:
            flush()
    flush()
    if pending:
        fenced.append(pending)
    return prose, fenced, headings


def code_spans(text):
    """Yield (start, end, content) for each CommonMark code span in a prose block."""
    position = 0
    while True:
        opening = BACKTICKS.search(text, position)
        if not opening:
            return
        if opening.start() and text[opening.start() - 1] == "\\":
            position = opening.end()
            continue
        run = opening.group()
        closing = re.compile(rf"(?<!`){run}(?!`)").search(text, opening.end())
        if not closing:
            position = opening.end()
            continue
        content = text[opening.end():closing.start()].replace("\n", " ")
        if len(content) > 1 and content.startswith(" ") and content.endswith(" ") and content.strip():
            content = content[1:-1]
        yield opening.start(), closing.end(), content
        position = closing.end()


def prose_spans(prose):
    """Yield (line, content, adjacent span, command text, names a skill) for every code span.

    The adjacent span is the next span when only whitespace, `/`, or `, operation` separates
    them, as in MCP `voiceflow_agent` `get`. A span right after the word CLI reads as a
    `vf` command, as in CLI `agent get`. A span next to the word skill names a skill.
    """
    for start, block in prose:
        spans = list(code_spans(block))
        for index, (offset, end, content) in enumerate(spans):
            following = spans[index + 1] if index + 1 < len(spans) else None
            adjacent = following[2] if following and OPERATION_GAP.fullmatch(block[end:following[0]]) else None
            command = content
            if CLI_PREFIX.search(block[:offset]) and not re.match(r"\$?\s*vf\b", content):
                command = "vf " + content
            named_skill = bool(SKILL_BEFORE.search(block[:offset]) or SKILL_AFTER.match(block, end))
            yield start + block.count("\n", 0, offset), content, adjacent, command, named_skill


def edit_distance(first, second):
    previous = list(range(len(second) + 1))
    for index, char in enumerate(first, 1):
        current = [index]
        for other_index, other in enumerate(second, 1):
            current.append(min(previous[other_index] + 1, current[-1] + 1,
                               previous[other_index - 1] + (char != other)))
        previous = current
    return previous[-1]


def without_code(text):
    """Blank out code spans so links and names inside them are not read as Markdown."""
    for start, end, _ in code_spans(text):
        text = text[:start] + re.sub(r"[^\n]", " ", text[start:end]) + text[end:]
    return text


def cli_invocations(text):
    """Yield (command path, flags) for each `vf` command in a code span or a shell line."""
    for segment in SHELL_SEPARATOR.split(text):
        tokens = TOKEN.findall(segment)
        if tokens[:1] == ["$"]:
            tokens = tokens[1:]
        if tokens[:1] != ["vf"]:
            continue
        words = []
        for token in tokens[1:]:
            if not COMMAND_WORD.fullmatch(token):
                break
            words.append(token)
        flags = []
        for token in tokens[1 + len(words):]:
            name = token.split("=", 1)[0]
            if FLAG.fullmatch(name):
                flags.append(name)
        yield " ".join(words), flags


def slug(heading):
    """Return GitHub's anchor for a heading's text, before duplicate numbering."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    text = re.sub(r"<[^>]+>", "", text).replace("`", "").replace("*", "").strip().lower()
    text = "".join(char for char in text
                   if char in " -_" or unicodedata.category(char)[0] in "LNM")
    return text.replace(" ", "-")


def anchors(text):
    _, _, headings = parse(text)
    found, counts = set(), {}
    for heading in headings:
        base = slug(heading)
        anchor = base
        while anchor in found:
            counts[base] = counts.get(base, 0) + 1
            anchor = f"{base}-{counts[base]}"
        found.add(anchor)
    found.update(HTML_ANCHOR.findall(text))
    return found


class Checker:
    def __init__(self, root, surface):
        self.root = root.resolve()
        self.plugin = self.root / "voiceflow"
        self.skills = self.plugin / "skills"
        self.tools = {tool: set(names) for tool, names in surface["mcp"]["tools"].items()}
        self.refused = surface["mcp"]["refused"]
        self.commands = set(surface["cli"]["commands"])
        self.groups = {" ".join(command.split()[:size]) for command in self.commands
                       for size in range(1, len(command.split()))}
        self.skill_names = {path.parent.name for path in self.skills.glob("*/SKILL.md")}
        self.anchor_cache = {}

    def files(self):
        return sorted(self.plugin.rglob("*.md"), key=lambda path: path.as_posix())

    def check(self):
        problems = []
        for path in self.files():
            problems.extend(self.check_file(path))
        return problems

    def check_file(self, path):
        path = path.resolve()
        label = path.relative_to(self.root).as_posix()
        text = path.read_text(encoding="utf-8")
        prose, fenced, _ = parse(text)
        problems = []

        def report(number, reason):
            problems.append((number, f"{label}:{number}: {reason}"))

        for number, line in enumerate(text.splitlines(), 1):
            for match in INTERNAL_NAMES.finditer(line):
                report(number, f"internal name \"{match.group()}\" is not public")
        for number, content, adjacent, command, named_skill in prose_spans(prose):
            self.check_span(path, content, adjacent, command, named_skill, number, report)
        for start, block in prose:
            masked = without_code(block)
            for match in LINK.finditer(masked):
                self.check_link(path, match.group(1), start + masked.count("\n", 0, match.start()), report)
        for number, line in fenced:
            self.check_commands(line, number, report)
        return [message for _, message in sorted(problems, key=lambda item: item[0])]

    def check_span(self, path, content, adjacent, command, named_skill, number, report):
        tool = TOOL_SPAN.match(content)
        if tool:
            operation = tool.group(2)
            if operation is None and adjacent and OPERATION_SPAN.fullmatch(adjacent) \
                    and not adjacent.startswith("voiceflow_"):
                operation = adjacent
            self.check_operation(tool.group(1), operation, number, report)
        if SKILL_SPAN.fullmatch(content) and content not in self.skill_names and (
                named_skill or any(edit_distance(content, name) <= 2 for name in self.skill_names)):
            report(number, f"unknown skill \"{content}\"")
        if MD_PATH_SPAN.fullmatch(content):
            self.check_md_path(path, content, number, report)
        self.check_commands(command, number, report)

    def check_operation(self, tool, operation, number, report):
        if tool not in self.tools:
            report(number, f"unknown MCP tool \"{tool}\"")
            return
        if operation is None:
            return
        reference = f"{tool}.{operation}"
        if operation not in self.tools[tool]:
            report(number, f"unknown MCP operation \"{reference}\"")
            return
        refusal = self.refused.get(reference)
        if refusal and refusal["when"] == "always":
            command = f"; name the CLI command \"vf {refusal['cli']}\" instead" if refusal.get("cli") else ""
            report(number, f"MCP always refuses \"{reference}\"{command}")

    def check_commands(self, text, number, report):
        for command, _ in cli_invocations(text):
            if command and command not in self.commands and command not in self.groups:
                report(number, f"unknown CLI command \"vf {command}\"")

    def check_md_path(self, path, reference, number, report):
        relative = path.relative_to(self.skills).parts if path.is_relative_to(self.skills) else ()
        skill_root = self.skills / relative[0] if len(relative) > 1 else path.parent
        for base in (path.parent, skill_root):
            target = (base / reference).resolve()
            if target.is_relative_to(self.plugin) and target.is_file():
                return
        report(number, f"missing file \"{reference}\"")

    def check_link(self, path, link, number, report):
        if "://" in link or link.startswith(("mailto:", "<")):
            return
        target_text, _, anchor = link.partition("#")
        if target_text:
            target = (path.parent / unquote(target_text)).resolve()
            if not target.is_relative_to(self.plugin):
                report(number, f"link leaves the plugin \"{link}\"")
                return
            if not target.is_file():
                report(number, f"missing link target \"{link}\"")
                return
        else:
            target = path
        if anchor and target.suffix == ".md" and unquote(anchor) not in self.anchors(target):
            report(number, f"missing anchor \"#{anchor}\" in {target.relative_to(self.root).as_posix()}")

    def anchors(self, path):
        if path not in self.anchor_cache:
            self.anchor_cache[path] = anchors(path.read_text(encoding="utf-8"))
        return self.anchor_cache[path]


def check_references(root, surface=None):
    """Return every reference problem under root/voiceflow as `path:line: reason` lines."""
    return Checker(root, surface if surface is not None else load_surface(root)).check()


def cli_uses(root):
    """Yield (path:line, command path, flags) for every `vf` command the packaged Markdown names."""
    root = root.resolve()
    for path in sorted((root / "voiceflow").rglob("*.md"), key=lambda path: path.as_posix()):
        prose, fenced, _ = parse(path.read_text(encoding="utf-8"))
        label = path.relative_to(root).as_posix()
        lines = [(number, command) for number, _, _, command, _ in prose_spans(prose)]
        for number, text in sorted(lines + fenced):
            for command, flags in cli_invocations(text):
                if command or flags:
                    yield f"{label}:{number}", command, flags
